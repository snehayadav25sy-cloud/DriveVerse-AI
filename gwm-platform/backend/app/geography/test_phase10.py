"""
Phase 10 tests — End-to-end caching (graph + OpenDRIVE)

Run:
    python gwm-platform/backend/app/geography/test_phase10.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.cache import compute_cache_key, cache_exists, list_cache_entries
from app.geography.graph import build_graph_from_osm, graph_hash
from app.geography.projection import project_graph
from app.geography.opendrive import OpenDriveCompiler
from app.geography.validator import OpenDriveValidator

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def _pipeline(lat: float, lon: float, radius_m: float):
    provider = OverpassProvider()
    raw = provider.download_radius(lat, lon, radius_m)
    roads = provider.fetch_roads()
    intersections = provider.fetch_intersections()
    graph = build_graph_from_osm(roads, intersections)
    projected = project_graph(graph, lat, lon)
    compiler = OpenDriveCompiler(projected)
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "map.xodr")
        meta = compiler.compile(out_path)
        validator = OpenDriveValidator()
        vresult = validator.validate(out_path)
        return graph, projected, meta, vresult


def test_10_1_cache_speedup():
    """10.1 Time first build vs repeated identical build."""
    print("\n[10.1] Timing first build vs cached build")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        check(False, "Geocode failed")
        return
    lat = resolution.latitude
    lon = resolution.longitude

    t0 = time.perf_counter()
    graph1, proj1, meta1, v1 = _pipeline(lat, lon, 500.0)
    t1 = time.perf_counter()
    first_ms = (t1 - t0) * 1000.0

    t2 = time.perf_counter()
    graph2, proj2, meta2, v2 = _pipeline(lat, lon, 500.0)
    t3 = time.perf_counter()
    second_ms = (t3 - t2) * 1000.0

    print(f"    First run:   {first_ms:.1f} ms")
    print(f"    Second run:  {second_ms:.1f} ms")
    print(f"    Speedup:     {first_ms / second_ms:.1f}x")

    check(second_ms < first_ms, f"Second run faster ({second_ms:.1f}ms < {first_ms:.1f}ms)")
    check(graph_hash(graph1) == graph_hash(graph2), "Graphs identical")
    check(meta1["xodr_hash"] == meta2["xodr_hash"], "OpenDRIVE hashes identical")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 10 - End-to-End Caching Tests")
    print("=" * 65)

    try:
        test_10_1_cache_speedup()
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
