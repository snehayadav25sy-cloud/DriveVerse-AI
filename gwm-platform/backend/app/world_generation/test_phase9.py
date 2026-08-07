"""
Phase 9 tests — Scenario event engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.events import ScenarioEventEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_9_1_event_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = ScenarioEventEngine(plan)
    events = engine.generate(event_count=5)
    check(len(events) > 0, f"Generated events: {len(events)}")

def test_9_2_event_types():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = ScenarioEventEngine(plan)
    events = engine.generate(event_count=10)
    types = {e.event_type for e in events}
    check(len(types) > 1, f"Multiple event types: {types}")

def test_9_3_deterministic():
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    e1 = ScenarioEventEngine(plan1)
    e2 = ScenarioEventEngine(plan2)
    ev1 = e1.generate(event_count=5)
    ev2 = e2.generate(event_count=5)
    check(len(ev1) == len(ev2), f"Deterministic count: {len(ev1)}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 9 - Scenario Event Tests")
    print("=" * 65)
    try:
        test_9_1_event_generation()
        test_9_2_event_types()
        test_9_3_deterministic()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

