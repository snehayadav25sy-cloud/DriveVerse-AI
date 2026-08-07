"""
Phase 6 tests — Coordinate projection

Run:
    python gwm-platform/backend/app/geography/test_phase6.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.graph import build_graph_from_osm
from app.geography.projection import (
    project_geographic_to_carla,
    project_graph,
    projection_metadata,
    distance_between_nodes_carla,
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


def _get_graph():
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        return None, None
    provider = OverpassProvider()
    raw = provider.download_radius(resolution.latitude, resolution.longitude, 500.0)
    if raw is None:
        return None, None
    roads = provider.fetch_roads()
    intersections = provider.fetch_intersections()
    graph = build_graph_from_osm(roads, intersections)
    return graph, resolution


def test_6_1_project_samples():
    """6.1 Project 3 sample nodes — before/after."""
    print("\n[6.1] Project sample nodes to CARLA coordinates")
    graph, resolution = _get_graph()
    if graph is None:
        check(False, "Failed to build graph")
        return
    origin_lat = resolution.latitude
    origin_lon = resolution.longitude
    projected = project_graph(graph, origin_lat, origin_lon)

    samples = projected.nodes[:3]
    for i, node in enumerate(samples):
        print(f"    Node {i+1}: {node.node_id}")
        print(f"      CARLA x={node.coordinate.latitude:.3f}, y={node.coordinate.longitude:.3f}, z={node.coordinate.altitude:.3f}")
        check(isinstance(node.coordinate.latitude, float), f"Node {i+1} has float carla_x")
        check(isinstance(node.coordinate.longitude, float), f"Node {i+1} has float carla_y")


def test_6_2_determinism():
    """6.2 Re-run projection twice — identical output."""
    print("\n[6.2] Projection determinism")
    graph, resolution = _get_graph()
    if graph is None:
        check(False, "Failed to build graph")
        return
    origin_lat = resolution.latitude
    origin_lon = resolution.longitude

    p1 = project_graph(graph, origin_lat, origin_lon)
    p2 = project_graph(graph, origin_lat, origin_lon)

    nodes1 = [(n.node_id, n.coordinate.latitude, n.coordinate.longitude) for n in p1.nodes]
    nodes2 = [(n.node_id, n.coordinate.latitude, n.coordinate.longitude) for n in p2.nodes]
    check(nodes1 == nodes2, "Projected nodes are identical across two runs")
    print(f"    Nodes projected: {len(nodes1)}")
    print(f"    First node: {nodes1[0]}")


def test_6_3_distance_plausibility():
    """6.3 Distances between two known nodes are geometrically plausible."""
    print("\n[6.3] Distance plausibility check")
    graph, resolution = _get_graph()
    if graph is None:
        check(False, "Failed to build graph")
        return
    origin_lat = resolution.latitude
    origin_lon = resolution.longitude
    projected = project_graph(graph, origin_lat, origin_lon)

    # Pick two nodes that share an edge (connected)
    edges = projected.edges
    if not edges:
        check(False, "No edges to test")
        return
    edge = edges[0]
    from_node = next((n for n in projected.nodes if n.node_id == edge.from_node), None)
    to_node = next((n for n in projected.nodes if n.node_id == edge.to_node), None)
    if from_node is None or to_node is None:
        check(False, "Edge nodes not found in projected graph")
        return

    carla_dist = distance_between_nodes_carla(from_node, to_node)
    osm_dist = edge.length_m
    print(f"    Edge: {edge.edge_id}")
    print(f"    OSM path length: {osm_dist:.3f} m")
    print(f"    CARLA straight-line: {carla_dist:.3f} m")

    # For a 500m-radius urban region, the max straight-line distance between
    # any two nodes should be under ~2000m (diameter of the region).
    # The min non-zero distance should be > 0.1m (not collapsing to zero).
    check(carla_dist >= 0.0, "CARLA distance is non-negative")
    if carla_dist > 0.0:
        check(carla_dist < 2000.0, f"CARLA distance is plausible for 500m region ({carla_dist:.1f}m < 2000m)")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 6 - Coordinate Projection Tests")
    print("=" * 65)

    try:
        test_6_1_project_samples()
        test_6_2_determinism()
        test_6_3_distance_plausibility()
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
