"""
Phase 1 tests — World models validation (Pydantic v2)

Run:
    python gwm-platform/backend/app/world_generation/test_phase1.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import (
    WorldCoordinate,
    WorldBoundingBox,
    AssetReference,
    BuildingPlan,
    VegetationPlan,
    StreetFurniturePlan,
    SignPlan,
    TrafficLightPlan,
    VehiclePlan,
    PedestrianPlan,
    ScenarioEvent,
    SensorConfig,
    WorldPlan,
    WorldProvenance,
)

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_1_1_valid_world_plan():
    """1.1 Valid world plan instantiation."""
    print("\n[1.1] Valid world plan instantiation")
    coord = WorldCoordinate(x=10.0, y=20.0, z=0.0)
    check(coord.x == 10.0, "WorldCoordinate created")

    bbox = WorldBoundingBox(min_x=0, max_x=100, min_y=0, max_y=50, min_z=0, max_z=10)
    check(bbox.max_x == 100.0, "WorldBoundingBox created")

    asset = AssetReference(semantic_class="palm_tree", resolved_asset_id="static.prop.palm_01")
    check(asset.semantic_class == "palm_tree", "AssetReference created")

    building = BuildingPlan(
        building_id="b1",
        semantic_type="residential",
        footprint=[(0, 0), (10, 0), (10, 10), (0, 10)],
        height_m=15.0,
        asset=asset,
    )
    check(building.height_m == 15.0, "BuildingPlan created")

    veg = VegetationPlan(vegetation_id="v1", semantic_type="palm", position=coord, asset=asset)
    check(veg.vegetation_id == "v1", "VegetationPlan created")

    furniture = StreetFurniturePlan(furniture_id="f1", semantic_type="lamp_post", position=coord)
    check(furniture.furniture_id == "f1", "StreetFurniturePlan created")

    sign = SignPlan(sign_id="s1", sign_type="speed_limit", value=50, position=coord, country="india")
    check(sign.value == 50.0, "SignPlan created")

    tl = TrafficLightPlan(traffic_light_id="tl1", position=coord, phase_duration_s=45.0, country="india")
    check(tl.phase_duration_s == 45.0, "TrafficLightPlan created")

    vehicle = VehiclePlan(vehicle_id="v1", semantic_type="sedan", position=coord, is_ego=True)
    check(vehicle.is_ego is True, "VehiclePlan created")

    pedestrian = PedestrianPlan(pedestrian_id="p1", position=coord, walking_speed_ms=1.5)
    check(pedestrian.walking_speed_ms == 1.5, "PedestrianPlan created")

    event = ScenarioEvent(event_id="e1", event_type="lane_closure", duration_s=120.0, severity=0.8)
    check(event.event_type == "lane_closure", "ScenarioEvent created")

    sensor = SensorConfig(sensor_id="cam1", sensor_type="rgb", position=coord, resolution=(1280, 720))
    check(sensor.resolution == (1280, 720), "SensorConfig created")

    plan = WorldPlan(
        world_id="world_001",
        seed=12345,
        location_query="MG Road, Bengaluru",
        country="india",
        map_name="Town01",
        carla_coordinate_origin=coord,
        buildings=[building],
        vegetation=[veg],
        street_furniture=[furniture],
        signs=[sign],
        traffic_lights=[tl],
        vehicles=[vehicle],
        pedestrians=[pedestrian],
        events=[event],
        sensors=[sensor],
        seeds={"world": 123, "traffic": 456},
    )
    check(plan.world_id == "world_001", "WorldPlan created")
    check(plan.plan_hash() != "", "WorldPlan hash generated")

    prov = WorldProvenance(
        country_profile_hash="abc123",
        geography_hash="def456",
        world_plan_hash="ghi789",
        asset_registry_hash="jkl012",
        world_seed=123,
        traffic_seed=456,
        pedestrian_seed=789,
        weather_seed=321,
        asset_seed=654,
        scenario_seed=987,
    )
    check(prov.world_seed == 123, "WorldProvenance created")
    check(prov.provenance_hash() != "", "WorldProvenance hash generated")


def test_1_2_invalid_bounding_box():
    """1.2 BoundingBox with min > max."""
    print("\n[1.2] Invalid BoundingBox")
    try:
        WorldBoundingBox(min_x=100, max_x=0, min_y=0, max_y=50, min_z=0, max_z=10)
        check(False, "Should have rejected max_x < min_x")
    except Exception as e:
        check(True, f"Rejected max_x < min_x: {type(e).__name__}")


def test_1_3_invalid_vehicle_speed():
    """1.3 Negative speed."""
    print("\n[1.3] Invalid vehicle speed")
    try:
        VehiclePlan(vehicle_id="v1", semantic_type="sedan", position=WorldCoordinate(x=0, y=0), speed_ms=-10.0)
        check(False, "Should have rejected negative speed")
    except Exception as e:
        check(True, f"Rejected negative speed: {type(e).__name__}")


def test_1_4_invalid_seed():
    """1.4 Negative seed."""
    print("\n[1.4] Invalid seed")
    try:
        WorldPlan(
            world_id="w1",
            seed=-1,
            location_query="test",
            country="usa",
            map_name="Town01",
            carla_coordinate_origin=WorldCoordinate(x=0, y=0),
        )
        check(False, "Should have rejected negative seed")
    except Exception as e:
        check(True, f"Rejected negative seed: {type(e).__name__}")


def test_1_5_invalid_sensor_config():
    """1.5 Invalid sensor configuration."""
    print("\n[1.5] Invalid sensor config")
    try:
        SensorConfig(sensor_id="cam1", sensor_type="rgb", position=WorldCoordinate(x=0, y=0), resolution=(-1, 720))
        check(False, "Should have rejected negative resolution width")
    except Exception as e:
        check(True, f"Rejected negative resolution: {type(e).__name__}")


def test_1_6_deterministic_hash():
    """1.6 WorldPlan hash is deterministic."""
    print("\n[1.6] Deterministic WorldPlan hash")
    coord = WorldCoordinate(x=0, y=0, z=0)
    plan1 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01", carla_coordinate_origin=coord)
    plan2 = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01", carla_coordinate_origin=coord)
    h1 = plan1.plan_hash()
    h2 = plan2.plan_hash()
    check(h1 == h2, f"Hashes match: {h1[:16]}...")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 1 - World Models Validation")
    print("=" * 65)

    try:
        test_1_1_valid_world_plan()
        test_1_2_invalid_bounding_box()
        test_1_3_invalid_vehicle_speed()
        test_1_4_invalid_seed()
        test_1_5_invalid_sensor_config()
        test_1_6_deterministic_hash()
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

