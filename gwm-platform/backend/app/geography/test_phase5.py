"""
Phase 5 tests — Road graph construction

Run:
    python gwm-platform/backend/app/geography/test_phase5.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.graph import build_graph_from_osm, graph_hash

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def _get_osm_data():
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        return None
    provider = OverpassProvider()
    raw = provider.download_radius(resolution.latitude, resolution.longitude, 500.0)
    if raw is None:
        return None
    roads = provider.fetch_roads()
    intersections = provider.fetch_intersections()
    return roads, intersections


def test_5_1_build_graph():
    """5.1 Build graph from Phase 3 region."""
    print("\n[5.1] Build graph from OSM data")
    data = _get_osm_data()
    if data is None:
        check(False, "Failed to get OSM data")
        return
    roads, intersections = data
    graph = build_graph_from_osm(roads, intersections)
    node_count = graph.node_count()
    edge_count = graph.edge_count()
    print(f"    Nodes: {node_count}")
    print(f"    Edges: {edge_count}")
    check(node_count > 0, f"Graph has nodes ({node_count})")
    check(edge_count > 0, f"Graph has edges ({edge_count})")


def test_5_2_detect_topology():
    """5.2 Detect intersections, dead ends, merges/splits."""
    print("\n[5.2] Detect topology categories")
    data = _get_osm_data()
    if data is None:
        check(False, "Failed to get OSM data")
        return
    roads, intersections = data
    graph = build_graph_from_osm(roads, intersections)

    intersections_found = sum(1 for n in graph.nodes if n.node_type == "intersection")
    dead_ends = sum(1 for n in graph.nodes if n.node_type == "dead_end")
    merges = sum(1 for n in graph.nodes if n.node_type == "merge")
    splits = sum(1 for n in graph.nodes if n.node_type == "split")
    endpoints = sum(1 for n in graph.nodes if n.node_type == "endpoint")

    print(f"    intersections: {intersections_found}")
    print(f"    dead_ends:     {dead_ends}")
    print(f"    merges:        {merges}")
    print(f"    splits:        {splits}")
    print(f"    endpoints:     {endpoints}")
    check(intersections_found >= 0, f"intersections={intersections_found}")
    check(dead_ends >= 0, f"dead_ends={dead_ends}")
    check(merges >= 0, f"merges={merges}")
    check(splits >= 0, f"splits={splits}")
    check(len(graph.nodes) == intersections_found + dead_ends + merges + splits + endpoints,
          "Node type counts sum to total nodes")


def test_5_3_determinism():
    """5.3 Build graph twice on identical input — deterministic hash."""
    print("\n[5.3] Determinism check")
    data = _get_osm_data()
    if data is None:
        check(False, "Failed to get OSM data")
        return
    roads, intersections = data

    graph1 = build_graph_from_osm(roads, intersections)
    graph2 = build_graph_from_osm(roads, intersections)

    hash1 = graph_hash(graph1)
    hash2 = graph_hash(graph2)

    print(f"    Run 1 hash: {hash1[:16]}...")
    print(f"    Run 2 hash: {hash2[:16]}...")
    check(hash1 == hash2, "Graph hashes are identical across two runs")
    check(graph1.node_count() == graph2.node_count(), "Node counts match")
    check(graph1.edge_count() == graph2.edge_count(), "Edge counts match")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 5 - Road Graph Construction Tests")
    print("=" * 65)

    try:
        test_5_1_build_graph()
        test_5_2_detect_topology()
        test_5_3_determinism()
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
