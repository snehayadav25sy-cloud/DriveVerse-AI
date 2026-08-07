"""
Phase 5 tests — Street furniture engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.furniture import StreetFurnitureEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_5_1_furniture_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = StreetFurnitureEngine(plan)
    plans = engine.generate(density=0.3)
    check(len(plans) > 0, f"Generated furniture: {len(plans)}")
    valid_types = {"lamp_post", "barrier", "bollard", "bench", "parking_meter", "trash_bin", "guard_rail"}
    for p in plans:
        check(p.semantic_type in valid_types, f"Valid furniture type: {p.semantic_type}")

def test_5_2_no_lane_placement():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    engine = StreetFurnitureEngine(plan)
    plans = engine.generate(density=0.3)
    for p in plans:
        check(p.position.x != 0.0 or p.position.y != 0.0, "Not placed at origin (safety margin)")

def test_5_3_deterministic():
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    e1 = StreetFurnitureEngine(plan1)
    e2 = StreetFurnitureEngine(plan2)
    p1 = e1.generate(density=0.3)
    p2 = e2.generate(density=0.3)
    check(len(p1) == len(p2), f"Deterministic count: {len(p1)}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 5 - Street Furniture Tests")
    print("=" * 65)
    try:
        test_5_1_furniture_generation()
        test_5_2_no_lane_placement()
        test_5_3_deterministic()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

