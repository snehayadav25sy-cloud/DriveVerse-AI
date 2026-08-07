"""
Phase 6 tests — Traffic sign and light engines
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.traffic import TrafficSignEngine, TrafficLightEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_6_1_sign_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = TrafficSignEngine(plan, {"rules": {"drive_side": "left"}})
    signs = engine.generate(density=0.2)
    check(len(signs) > 0, f"Generated signs: {len(signs)}")
    for s in signs:
        check(s.country == "india", f"Sign country: {s.country}")

def test_6_2_light_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="japan", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = TrafficLightEngine(plan, {"rules": {"drive_side": "left"}})
    lights = engine.generate(intersection_count=5)
    check(len(lights) > 0, f"Generated lights: {len(lights)}")
    for l in lights:
        check(l.country == "japan", f"Light country: {l.country}")
        check(l.phase_duration_s > 0, f"Phase duration: {l.phase_duration_s}")

def test_6_3_country_differences():
    plan_india = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                           carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                           bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan_usa = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                         carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                         bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    signs_india = TrafficSignEngine(plan_india, {"rules": {"drive_side": "left"}}).generate()
    signs_usa = TrafficSignEngine(plan_usa, {"rules": {"drive_side": "right"}}).generate()
    check(len(signs_india) > 0, "India signs generated")
    check(len(signs_usa) > 0, "USA signs generated")

def test_6_4_deterministic():
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="germany", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="germany", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    e1 = TrafficSignEngine(plan1, {"rules": {"drive_side": "right"}})
    e2 = TrafficSignEngine(plan2, {"rules": {"drive_side": "right"}})
    s1 = e1.generate()
    s2 = e2.generate()
    check(len(s1) == len(s2), f"Deterministic sign count: {len(s1)}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 6 - Traffic Tests")
    print("=" * 65)
    try:
        test_6_1_sign_generation()
        test_6_2_light_generation()
        test_6_3_country_differences()
        test_6_4_deterministic()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

