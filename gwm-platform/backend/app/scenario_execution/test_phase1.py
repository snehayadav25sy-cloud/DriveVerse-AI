"""
Phase 1 tests — Execution models
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.models import (
    ExecutionSession,
    SessionStatus,
    ActorStatus,
    ActorType,
    EventType,
    TriggerType,
    MapProviderType,
    MapDeploymentStatus,
    VehicleActorState,
    PedestrianActorState,
    ScenarioEventPlan,
    EventTrigger,
    SensorState,
    ExecutionPreflightReport,
    DatasetValidationReport,
    RecordingManifest,
    FrameIndexEntry,
    Checkpoint,
    ExecutionProvenance,
    ExecutionError,
    ExecutionCoordinate,
)

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_1_1_session_creation():
    session = ExecutionSession(
        session_id="s1",
        seeds={"master_seed": 42, "traffic_seed": 43, "spawn_seed": 44, "event_seed": 45, "weather_seed": 46, "sensor_seed": 47},
    )
    check(session.session_id == "s1", "Session created")
    check(session.status == SessionStatus.CREATED, "Initial status is CREATED")
    check(session.seeds["master_seed"] == 42, "Seeds preserved")

def test_1_2_actor_models():
    v = VehicleActorState(actor_id="v1", semantic_class="sedan", blueprint_id="vehicle.tesla.model3", is_ego=True, position=ExecutionCoordinate(x=0, y=0, z=0))
    check(v.actor_type == ActorType.VEHICLE, "Vehicle actor type")
    check(v.is_ego is True, "Ego flag")
    p = PedestrianActorState(actor_id="p1", semantic_class="pedestrian", walking_speed_ms=1.5, position=ExecutionCoordinate(x=0, y=0, z=0))
    check(p.actor_type == ActorType.PEDESTRIAN, "Pedestrian actor type")
    check(p.walking_speed_ms == 1.5, "Walking speed")

def test_1_3_event_models():
    event = ScenarioEventPlan(event_id="e1", event_type=EventType.VEHICLE_BRAKING, trigger=EventTrigger(trigger_type=TriggerType.TIME_TRIGGER), start_time_s=10.0, duration_s=5.0)
    check(event.event_type == EventType.VEHICLE_BRAKING, "Event type")
    check(event.start_time_s == 10.0, "Start time")

def test_1_4_sensor_model():
    sensor = SensorState(sensor_id="cam1", sensor_type="rgb", position=ExecutionCoordinate(x=0, y=0, z=1.4), resolution=(1280, 720))
    check(sensor.sensor_type == "rgb", "Sensor type")
    check(sensor.resolution == (1280, 720), "Resolution")

def test_1_5_enums():
    check(SessionStatus.CREATED.value == "CREATED", "SessionStatus.CREATED")
    check(ActorType.VEHICLE.value == "vehicle", "ActorType.VEHICLE")
    check(EventType.JAYWALKING.value == "JAYWALKING", "EventType.JAYWALKING")
    check(MapProviderType.TOWN.value == "town", "MapProviderType.TOWN")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 1 - Execution Models Tests")
    print("=" * 65)
    try:
        test_1_1_session_creation()
        test_1_2_actor_models()
        test_1_3_event_models()
        test_1_4_sensor_model()
        test_1_5_enums()
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
