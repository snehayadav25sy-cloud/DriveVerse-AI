"""
Phase 1 tests — Geographic schema validation (Pydantic v2)

Run:
    python gwm-platform/backend/app/geography/test_phase1.py
"""

import sys
import os

# Ensure backend root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.models import (
    GeoCoordinate,
    BoundingBox,
    LocationRequest,
    LocationResolution,
    Road,
    Lane,
    Intersection,
    TrafficSignal,
    Crosswalk,
    RoadNode,
    RoadEdge,
    RoadGraph,
    GeographicScenario,
    MapArtifact,
    MapProvenance,
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


def test_1_1_valid_instances():
    """1.1 Instantiate each model with valid data."""
    print("\n[1.1] Valid model instantiation")

    coord = GeoCoordinate(latitude=12.9716, longitude=77.5946, altitude=920.0)
    check(coord.latitude == 12.9716, "GeoCoordinate created")

    bbox = BoundingBox(south=12.97, north=12.98, west=77.59, east=77.60)
    check(bbox.south == 12.97, "BoundingBox created")

    loc_req = LocationRequest(location="MG Road, Bengaluru", radius_m=500.0, country="India")
    check(loc_req.location == "MG Road, Bengaluru", "LocationRequest created")

    loc_res = LocationResolution(
        query="MG Road, Bengaluru",
        provider="nominatim",
        latitude=12.9716,
        longitude=77.5946,
        display_name="MG Road, Bengaluru, India",
        country="India",
        country_code="IN",
        state="Karnataka",
        city="Bengaluru",
    )
    check(loc_res.country == "India", "LocationResolution created")

    road = Road(
        osm_id="way/12345",
        name="MG Road",
        highway_type="primary",
        lanes=3,
        maxspeed=50.0,
        oneway=True,
        surface="asphalt",
        bridge=False,
        tunnel=False,
        country="IN",
        geometry=[(77.5946, 12.9716), (77.5950, 12.9718)],
    )
    check(road.lanes == 3, "Road created")

    lane = Lane(id="lane_1", width=3.5, direction="forward", is_driving=True)
    check(lane.width == 3.5, "Lane created")

    inter = Intersection(
        node_id="node_1",
        latitude=12.9716,
        longitude=77.5946,
        incoming_roads=["way/12345"],
        outgoing_roads=["way/12346"],
        traffic_signal=True,
    )
    check(inter.traffic_signal is True, "Intersection created")

    sig = TrafficSignal(
        osm_id="node/999",
        latitude=12.9716,
        longitude=77.5946,
        signal_type="traffic_light",
        lanes=["lane_1"],
    )
    check(sig.signal_type == "traffic_light", "TrafficSignal created")

    cw = Crosswalk(
        osm_id="way/888",
        latitude=12.9716,
        longitude=77.5946,
        crossing_type="marked",
        lanes=["lane_1"],
    )
    check(cw.crossing_type == "marked", "Crosswalk created")

    node = RoadNode(
        node_id="node_1",
        coordinate=coord,
        node_type="intersection",
        roads=["way/12345"],
    )
    check(node.node_type == "intersection", "RoadNode created")

    edge = RoadEdge(
        edge_id="edge_1",
        from_node="node_1",
        to_node="node_2",
        road=road,
        length_m=250.0,
        lane_count=3,
    )
    check(edge.length_m == 250.0, "RoadEdge created")

    graph = RoadGraph(
        nodes=[node],
        edges=[edge],
        metadata={"source": "overpass"},
    )
    check(graph.node_count() == 1, "RoadGraph created")

    scenario = GeographicScenario(
        carla_map="Town01",
        sensors=["rgb", "lidar"],
        frames=500,
        location_query="MG Road, Bengaluru",
        origin_latitude=12.9716,
        origin_longitude=77.5946,
    )
    check(scenario.location_query == "MG Road, Bengaluru", "GeographicScenario created")

    artifact = MapArtifact(
        xodr_path="/tmp/test.xodr",
        xodr_size_bytes=1024,
        xodr_hash="abc123",
        validator_passed=True,
        carla_map_name="GeneratedMap",
        carla_load_succeeded=True,
        carla_spawn_point_count=42,
    )
    check(artifact.carla_spawn_point_count == 42, "MapArtifact created")

    prov = MapProvenance(
        location_query="MG Road, Bengaluru",
        radius_m=500.0,
        geocoder_provider="nominatim",
        osm_provider="overpass",
        resolved_latitude=12.9716,
        resolved_longitude=77.5946,
        resolved_country="India",
    )
    check(prov.resolved_country == "India", "MapProvenance created")


def test_1_2_impossible_coordinates():
    """1.2 LocationRequest with lat=200, lon=-500 — must reject."""
    print("\n[1.2] Impossible coordinates in LocationRequest")
    try:
        LocationRequest(latitude=200.0, longitude=-500.0)
        check(False, "Should have rejected lat=200, lon=-500")
    except Exception as e:
        check(True, f"Rejected impossible coords: {type(e).__name__}")


def test_1_3_bbox_min_max():
    """1.3 BoundingBox with min > max — must reject."""
    print("\n[1.3] BoundingBox with min > max")
    try:
        BoundingBox(south=12.98, north=12.97, west=77.59, east=77.60)
        check(False, "Should have rejected north < south")
    except Exception as e:
        check(True, f"Rejected north < south: {type(e).__name__}")

    try:
        BoundingBox(south=12.97, north=12.98, west=77.60, east=77.59)
        check(False, "Should have rejected east < west")
    except Exception as e:
        check(True, f"Rejected east < west: {type(e).__name__}")


def test_1_4_negative_radius():
    """1.4 LocationRequest with negative radius — must reject."""
    print("\n[1.4] Negative radius")
    try:
        LocationRequest(location="MG Road, Bengaluru", radius_m=-100.0)
        check(False, "Should have rejected negative radius")
    except Exception as e:
        check(True, f"Rejected negative radius: {type(e).__name__}")


def test_1_5_empty_location():
    """1.5 LocationRequest with no location info — must reject."""
    print("\n[1.5] Empty location")
    try:
        LocationRequest(location="   ", radius_m=500.0)
        check(False, "Should have rejected whitespace-only location")
    except Exception as e:
        check(True, f"Rejected empty location: {type(e).__name__}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 1 - Geographic Schema Validation")
    print("=" * 65)

    try:
        test_1_1_valid_instances()
        test_1_2_impossible_coordinates()
        test_1_3_bbox_min_max()
        test_1_4_negative_radius()
        test_1_5_empty_location()
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
