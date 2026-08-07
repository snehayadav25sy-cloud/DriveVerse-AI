"""
Phase 15 tests — Build 6 integration: WorldPlan -> ExecutionSession
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.models import ExecutionSession, ExecutionCoordinate, ActorType, SensorState
from app.scenario_execution.orchestrator import ScenarioOrchestrator
from app.world_generation.models import WorldPlan, VehiclePlan, PedestrianPlan, SensorConfig, WorldCoordinate

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_15_1_worldplan_to_session():
    world_plan = WorldPlan(
        world_id="world_001",
        seed=42,
        location_query="Mumbai, India",
        country="india",
        map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        vehicles=[
            VehiclePlan(vehicle_id="v1", semantic_type="sedan", blueprint_id="vehicle.tesla.model3", position=WorldCoordinate(x=0, y=0, z=0), is_ego=True),
            VehiclePlan(vehicle_id="v2", semantic_type="suv", position=WorldCoordinate(x=10, y=0, z=0)),
        ],
        pedestrians=[
            PedestrianPlan(pedestrian_id="p1", position=WorldCoordinate(x=5, y=5, z=0)),
        ],
        sensors=[
            SensorConfig(sensor_id="cam1", sensor_type="rgb", position=WorldCoordinate(x=0, y=0, z=1.4), resolution=(1280, 720)),
        ],
    )
    resolved_scenario = {"country": "india", "weather": "rain", "scenario_id": "scenario_001"}
    orchestrator = ScenarioOrchestrator()
    session = orchestrator.create_session(world_plan, resolved_scenario)
    session = orchestrator.prepare_session(session, world_plan)
    check(session.scenario_id == "scenario_001", "Scenario ID preserved")
    check(session.world_plan_id == "world_001", "World plan ID preserved")
    check(len(session.actors) == 3, "Three actors planned")
    check(len(session.sensors) == 1, "One sensor planned")

def test_15_2_no_schema_drift():
    world_plan = WorldPlan(
        world_id="world_002",
        seed=42,
        location_query="Test",
        country="usa",
        map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
    )
    resolved_scenario = {"country": "usa", "weather": "sunny"}
    orchestrator = ScenarioOrchestrator()
    session = orchestrator.create_session(world_plan, resolved_scenario)
    check(hasattr(session, 'session_id'), "Session has session_id")
    check(hasattr(session, 'status'), "Session has status")
    check(hasattr(session, 'actors'), "Session has actors")
    check(hasattr(session, 'sensors'), "Session has sensors")
    check(hasattr(session, 'events'), "Session has events")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 15 - Build 6 Integration Tests")
    print("=" * 65)
    try:
        test_15_1_worldplan_to_session()
        test_15_2_no_schema_drift()
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
