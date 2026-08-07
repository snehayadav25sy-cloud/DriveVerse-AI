"""
Phase 7 tests — Vehicle population engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.vehicles import VehiclePopulationEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_7_1_vehicle_generation():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="india", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    profile = {"vehicle_mix": {"sedan": 0.4, "motorcycle": 0.3, "bus": 0.2, "auto_rickshaw": 0.1}}
    engine = VehiclePopulationEngine(plan, profile, {})
    vehicles = engine.generate(traffic_density="heavy")
    check(len(vehicles) > 0, f"Generated vehicles: {len(vehicles)}")

def test_7_2_traffic_density():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    profile = {"vehicle_mix": {"sedan": 0.5, "suv": 0.3, "truck": 0.2}}
    engine = VehiclePopulationEngine(plan, profile, {})
    low = engine.generate(traffic_density="low")
    heavy = engine.generate(traffic_density="heavy")
    check(len(heavy) > len(low), f"Heavy ({len(heavy)}) > Low ({len(low)})")

def test_7_3_deterministic():
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="germany", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="germany", map_name="Town01",
                      carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                      bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    profile = {"vehicle_mix": {"sedan": 0.5, "suv": 0.3, "truck": 0.2}}
    e1 = VehiclePopulationEngine(plan1, profile, {})
    e2 = VehiclePopulationEngine(plan2, profile, {})
    v1 = e1.generate()
    v2 = e2.generate()
    check(len(v1) == len(v2), f"Deterministic count: {len(v1)}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 7 - Vehicle Population Tests")
    print("=" * 65)
    try:
        test_7_1_vehicle_generation()
        test_7_2_traffic_density()
        test_7_3_deterministic()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

