"""
Phase 3 tests — Building placement engine
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.placement import BuildingPlacementEngine

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_3_1_basic_placement():
    plan = WorldPlan(
        world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100, min_z=0, max_z=10),
    )
    engine = BuildingPlacementEngine(plan)
    osm_buildings = [
        {"osm_id": "b1", "building": "residential", "geometry": [(0, 0), (10, 0), (10, 10), (0, 10)]},
        {"osm_id": "b2", "building": "commercial", "geometry": [(20, 0), (30, 0), (30, 10), (20, 10)]},
        {"osm_id": "b3", "building": "school", "geometry": [(40, 0), (50, 0), (50, 15), (40, 15)]},
    ]
    plans = engine.place_from_osm_buildings(osm_buildings)
    check(len(plans) == 3, f"Placed 3 buildings, got {len(plans)}")


def test_3_2_semantic_mapping():
    plan = WorldPlan(
        world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100, min_z=0, max_z=10),
    )
    engine = BuildingPlacementEngine(plan)
    semantic = engine._osm_to_semantic("residential")
    check(semantic == "residential", f"residential -> {semantic}")
    semantic = engine._osm_to_semantic("school")
    check(semantic == "education", f"school -> {semantic}")
    semantic = engine._osm_to_semantic("church")
    check(semantic == "religious", f"church -> {semantic}")
    semantic = engine._osm_to_semantic("unknown")
    check(semantic == "generic", f"unknown -> {semantic}")


def test_3_3_height_estimation():
    plan = WorldPlan(
        world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100, min_z=0, max_z=10),
    )
    engine = BuildingPlacementEngine(plan)
    h = engine._estimate_height("residential", {})
    check(h == 12.0, f"Residential height: {h}")
    h = engine._estimate_height("industrial", {"building:levels": "5"})
    check(h == 15.0, f"Industrial with levels: {h}")


def test_3_4_spacing_violation():
    plan = WorldPlan(
        world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
        carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
        bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100, min_z=0, max_z=10),
    )
    engine = BuildingPlacementEngine(plan, min_spacing_m=5.0)
    buildings = [
        {"osm_id": "b1", "building": "residential", "geometry": [(0, 0), (10, 0), (10, 10), (0, 10)]},
        {"osm_id": "b2", "building": "residential", "geometry": [(1, 1), (11, 1), (11, 11), (1, 11)]},
    ]
    plans = engine.place_from_osm_buildings(buildings)
    check(len(plans) == 1, f"Spacing violation filtered: {len(plans)}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 3 - Building Placement Tests")
    print("=" * 65)
    try:
        test_3_1_basic_placement()
        test_3_2_semantic_mapping()
        test_3_3_height_estimation()
        test_3_4_spacing_violation()
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



