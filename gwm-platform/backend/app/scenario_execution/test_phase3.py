"""
Phase 3 tests — Preflight validation
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import tempfile
from app.scenario_execution.models import ExecutionSession, TimingConfig, MapConfig, SessionStatus, ExecutionCoordinate, ActorState, SensorState, ActorType
from app.scenario_execution.preflight import PreflightValidator

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_3_1_valid_scenario():
    with tempfile.TemporaryDirectory() as tmpdir:
        actor1 = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
        actor2 = ActorState(actor_id="p1", actor_type=ActorType.PEDESTRIAN, semantic_class="pedestrian", position=ExecutionCoordinate(x=1, y=1, z=0))
        sensor1 = SensorState(sensor_id="cam1", sensor_type="rgb", position=ExecutionCoordinate(x=0, y=0, z=1.4))
        sensor2 = SensorState(sensor_id="lidar1", sensor_type="lidar", position=ExecutionCoordinate(x=0, y=0, z=1.4))
        session = ExecutionSession(
            session_id="s1",
            seeds={"master_seed": 1, "traffic_seed": 2, "spawn_seed": 3, "event_seed": 4, "weather_seed": 5, "sensor_seed": 6},
            timing=TimingConfig(fixed_delta_seconds=0.05, total_simulation_seconds=30.0),
            map=MapConfig(provider="town", map_name="Town01", deployment_required=False),
            recording={"output_directory": tmpdir},
            actors=[actor1, actor2],
            sensors=[sensor1, sensor2],
        )
        validator = PreflightValidator(session)
        report = validator.validate()
        check(report.passed is True, "Valid scenario passes preflight")

def test_3_2_missing_seeds():
    session = ExecutionSession(
        session_id="s1",
        seeds={"master_seed": 1},
        timing=TimingConfig(fixed_delta_seconds=0.05, total_simulation_seconds=30.0),
        recording={"output_directory": "/tmp/test"},
    )
    validator = PreflightValidator(session)
    report = validator.validate()
    check(report.passed is False, "Missing seeds fails preflight")

def test_3_3_deployment_required():
    actor = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
    sensor = SensorState(sensor_id="cam1", sensor_type="rgb", position=ExecutionCoordinate(x=0, y=0, z=1.4))
    session = ExecutionSession(
        session_id="s1",
        seeds={"master_seed": 1, "traffic_seed": 2, "spawn_seed": 3, "event_seed": 4, "weather_seed": 5, "sensor_seed": 6},
        timing=TimingConfig(fixed_delta_seconds=0.05, total_simulation_seconds=30.0),
        map=MapConfig(provider="opendrive_artifact", map_name="custom", deployment_required=True, deployment_instructions=["deploy map"]),
        recording={"output_directory": "/tmp/test"},
        actors=[actor],
        sensors=[sensor],
    )
    validator = PreflightValidator(session)
    report = validator.validate()
    check(report.passed is False, "Deployment required fails preflight")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 3 - Preflight Tests")
    print("=" * 65)
    try:
        test_3_1_valid_scenario()
        test_3_2_missing_seeds()
        test_3_3_deployment_required()
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
