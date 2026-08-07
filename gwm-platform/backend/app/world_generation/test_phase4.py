"""
Phase 4 tests — Vegetation engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.vegetation import VegetationEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_4_1_vegetation_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = VegetationEngine(plan)
    plans = engine.generate(density=0.5, season="summer")
    check(len(plans) > 0, f"Generated vegetation: {len(plans)}")

def test_4_2_country_profiles():
    for country in ["india", "dubai", "germany", "japan", "usa"]:
        plan = WorldPlan(world_id="w1", seed=42, location_query="test", country=country, map_name="Town01",
                         carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                         bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
        engine = VegetationEngine(plan)
        plans = engine.generate(density=0.5, season="summer")
        check(len(plans) > 0, f"{country}: {len(plans)} vegetation items")

def test_4_3_season_variation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = VegetationEngine(plan)
    summer = engine.generate(density=0.5, season="summer")
    winter = engine.generate(density=0.5, season="winter")
    check(len(winter) < len(summer), f"Winter ({len(winter)}) < Summer ({len(summer)})")

def test_4_4_deterministic():
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    e1 = VegetationEngine(plan1)
    e2 = VegetationEngine(plan2)
    p1 = e1.generate(density=0.5, season="summer")
    p2 = e2.generate(density=0.5, season="summer")
    check(len(p1) == len(p2), f"Deterministic count: {len(p1)} == {len(p2)}")
    if len(p1) > 0:
        check(p1[0].position.x == p2[0].position.x, "Deterministic position x")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 4 - Vegetation Engine Tests")
    print("=" * 65)
    try:
        test_4_1_vegetation_generation()
        test_4_2_country_profiles()
        test_4_3_season_variation()
        test_4_4_deterministic()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

