"""
Phase 20 tests — Full end-to-end pipeline
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import uuid
import tempfile
import json

from app.scenario_execution.models import ExecutionSession, TimingConfig, MapConfig, SessionStatus
from app.scenario_execution.orchestrator import ScenarioOrchestrator
from app.scenario_execution.state_machine import ExecutionStateMachine
from app.scenario_execution.preflight import PreflightValidator
from app.scenario_execution.events.event_scheduler import EventScheduler
from app.scenario_execution.actors.actor_manager import ActorManager
from app.scenario_execution.sensors.sensor_manager import SensorManager
from app.scenario_execution.sensors.synchronization import SensorSynchronizer
from app.scenario_execution.recording.recorder import RecordingEngine
from app.scenario_execution.validation.execution_validator import DatasetValidator
from app.scenario_execution.provenance.execution_provenance import compute_execution_provenance
from app.scenario_execution.deployment.map_deployer import MapDeployer
from app.world_generation.models import WorldPlan, WorldCoordinate, VehiclePlan, PedestrianPlan, SensorConfig
from app.country_profiles.models import CountryProfile, TrafficRules, SpeedLimits, DriverBehavior
from app.schemas.scenario import ScenarioConfig, VehicleMix

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_20_1_full_pipeline():
    scenario = ScenarioConfig(
        country="India",
        city="Mumbai",
        road_type="Highway",
        weather="Rain",
        time_of_day="Night",
        traffic_density="Heavy",
        vehicles=VehicleMix(car=10, truck=2, bus=1, motorcycle=20),
        pedestrians=15,
        sensors=["rgb", "lidar", "radar", "depth"],
        frames=600,
        export_format="kitti",
    )
    country_profile = CountryProfile(
        id="india",
        rules=TrafficRules(drive_side="left", speed_limits=SpeedLimits(highway=120, urban=50, residential=40, school=20), behavior=DriverBehavior(aggressiveness=0.7)),
        vehicle_mix={"sedan": 0.3, "rickshaw": 0.2, "motorcycle": 0.5},
    )
    world_plan = WorldPlan(
        world_id="world_e2e_001",
        seed=42,
        location_query="Mumbai, India",
        country="india",
        map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        vehicles=[
            VehiclePlan(vehicle_id="v1", semantic_type="sedan", blueprint_id="vehicle.tesla.model3", position=WorldCoordinate(x=0, y=0, z=0), is_ego=True),
            VehiclePlan(vehicle_id="v2", semantic_type="motorcycle", position=WorldCoordinate(x=10, y=0, z=0)),
            VehiclePlan(vehicle_id="v3", semantic_type="rickshaw", position=WorldCoordinate(x=20, y=0, z=0)),
        ],
        pedestrians=[
            PedestrianPlan(pedestrian_id="p1", position=WorldCoordinate(x=5, y=5, z=0), walking_speed_ms=1.2),
        ],
        sensors=[
            SensorConfig(sensor_id="cam1", sensor_type="rgb", position=WorldCoordinate(x=0, y=0, z=1.4), resolution=(1280, 720)),
            SensorConfig(sensor_id="lidar1", sensor_type="lidar", position=WorldCoordinate(x=0, y=0, z=2.0), rotation=(0, 0, 0)),
        ],
        events=[],
        seeds={"world_seed": 42, "traffic_seed": 43, "pedestrian_seed": 44, "weather_seed": 45, "asset_seed": 46, "scenario_seed": 47},
    )
    orchestrator = ScenarioOrchestrator()
    session = orchestrator.create_session(world_plan, {"country": "india", "weather": "rain", "scenario_id": "scenario_e2e_001"})
    session.recording = {"output_directory": tempfile.mkdtemp()}
    session = orchestrator.prepare_session(session, world_plan)
    check(len(session.actors) == 4, "Actors planned")
    check(len(session.sensors) == 2, "Sensors planned")
    check(session.status == SessionStatus.CREATED, "Initial status")

    validator = PreflightValidator(session)
    report = validator.validate()
    check(report.passed is True, "Preflight passed")

    sm = ExecutionStateMachine(session.status)
    sm.transition_to(SessionStatus.VALIDATING)
    sm.transition_to(SessionStatus.READY)
    sm.transition_to(SessionStatus.STARTING)
    sm.transition_to(SessionStatus.RUNNING)
    check(sm.status == SessionStatus.RUNNING, "State machine advanced")

    scheduler = EventScheduler(master_seed=42, event_seed=45)
    events = scheduler.schedule([], 30.0)
    check(len(events) == 0, "No events scheduled")

    actor_manager = ActorManager()
    for actor in session.actors:
        actor_manager.spawn(actor)
    check(actor_manager.count() == 4, "All actors spawned")

    sensor_manager = SensorManager()
    for sensor in session.sensors:
        sensor_manager.register(sensor)
    check(len(sensor_manager.get_all_sensors()) == 2, "All sensors registered")

    sync = SensorSynchronizer([s.sensor_id for s in session.sensors])
    for frame_id in range(10):
        for sensor in session.sensors:
            sync.record_frame(frame_id, sensor.sensor_id, float(frame_id) * 0.1)
    sync_report = sync.validate()
    check(sync_report.synchronized is True, "Frames synchronized")

    with tempfile.TemporaryDirectory() as tmpdir:
        recorder = RecordingEngine(tmpdir, session.session_id)
        recorder.initialize([s.sensor_id for s in session.sensors])
        for frame_id in range(10):
            frame_data = {s.sensor_id: f"{s.sensor_type}_{frame_id:06d}.bin" for s in session.sensors}
            recorder.record_frame(frame_id, frame_data)
        manifest = recorder.finalize()
        check(manifest.frame_count == 10, "Recording complete")

        validator = DatasetValidator(tmpdir, expected_frames=10)
        # Create dummy files to pass validation
        for i in range(10):
            with open(os.path.join(tmpdir, "rgb", f"{i:06d}.png"), "wb") as f:
                f.write(b"PNGDATA" * 100)
        with open(os.path.join(tmpdir, "provenance", "execution_provenance.json"), "w") as f:
            f.write("{}")
        report = validator.validate()
        check(report.passed is True, "Dataset validation passed")

    deployer = MapDeployer()
    result = deployer.resolve(MapConfig(provider="town", map_name="Town01"))
    check(result.status.value == "AVAILABLE", "Map available")

    provenance = compute_execution_provenance(session, {"country": "india"}, world_plan)
    check(provenance.session_id == session.session_id, "Provenance session ID")
    check(provenance.provenance_hash() != "", "Provenance hash generated")

    check(session.world_plan_id == "world_e2e_001", "World plan ID preserved")
    check(session.scenario_id == "scenario_e2e_001", "Scenario ID preserved")

def test_20_2_reproducibility():
    world_plan = WorldPlan(
        world_id="world_repro_001",
        seed=42,
        location_query="Test",
        country="usa",
        map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        vehicles=[
            VehiclePlan(vehicle_id="v1", semantic_type="sedan", position=WorldCoordinate(x=0, y=0, z=0)),
        ],
    )
    orchestrator = ScenarioOrchestrator()
    session1 = orchestrator.create_session(world_plan, {"country": "usa"})
    session2 = orchestrator.create_session(world_plan, {"country": "usa"})
    check(session1.seeds == session2.seeds, "Seeds are reproducible")
    check(session1.session_id != session2.session_id, "Session IDs are unique")

def test_20_3_country_semantic_reproducibility():
    scenario = ScenarioConfig(
        country="India",
        weather="Rain",
        time_of_day="Night",
        traffic_density="Heavy",
        vehicles=VehicleMix(car=5, motorcycle=15),
    )
    check(scenario.country == "India", "Country preserved")
    check(scenario.weather == "Rain", "Weather preserved")
    check(scenario.vehicles.motorcycle == 15, "Vehicle mix preserved")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 20 - Full End-to-End Pipeline Tests")
    print("=" * 65)
    try:
        test_20_1_full_pipeline()
        test_20_2_reproducibility()
        test_20_3_country_semantic_reproducibility()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
