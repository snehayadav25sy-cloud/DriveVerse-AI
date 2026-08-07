"""
Phase 5 tests — Actor manager
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.actors.actor_manager import ActorManager
from app.scenario_execution.models import ActorState, ActorType, ActorStatus, ExecutionCoordinate

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_5_1_spawn_and_track():
    manager = ActorManager()
    actor = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
    result = manager.spawn(actor)
    check(result is True, "Spawn succeeded")
    retrieved = manager.get_state("v1")
    check(retrieved is not None, "Actor tracked")
    check(retrieved.actor_id == "v1", "Correct actor retrieved")

def test_5_2_destroy():
    manager = ActorManager()
    actor = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
    manager.spawn(actor)
    result = manager.destroy("v1")
    check(result is True, "Destroy succeeded")
    retrieved = manager.get_state("v1")
    check(retrieved.status == ActorStatus.DESTROYED, "Actor marked destroyed")

def test_5_3_filter_by_type():
    manager = ActorManager()
    v = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
    p = ActorState(actor_id="p1", actor_type=ActorType.PEDESTRIAN, semantic_class="pedestrian", position=ExecutionCoordinate(x=1, y=1, z=0))
    manager.spawn(v)
    manager.spawn(p)
    vehicles = manager.get_actors_by_type(ActorType.VEHICLE)
    check(len(vehicles) == 1, "One vehicle")
    peds = manager.get_actors_by_type(ActorType.PEDESTRIAN)
    check(len(peds) == 1, "One pedestrian")

def test_5_4_health_check():
    manager = ActorManager()
    actor = ActorState(actor_id="v1", actor_type=ActorType.VEHICLE, semantic_class="sedan", position=ExecutionCoordinate(x=0, y=0, z=0))
    manager.spawn(actor)
    health = manager.health_check()
    check(health["v1"] is True, "Actor healthy")
    check(manager.count() == 1, "Count is 1")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 5 - Actor Manager Tests")
    print("=" * 65)
    try:
        test_5_1_spawn_and_track()
        test_5_2_destroy()
        test_5_3_filter_by_type()
        test_5_4_health_check()
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
