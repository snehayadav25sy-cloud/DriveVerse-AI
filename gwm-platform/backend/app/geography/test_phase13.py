"""
Phase 13 tests — Live OSM integration test

Run:
    python gwm-platform/backend/app/geography/test_phase13.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
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


def test_13_live_integration():
    """13: Live end-to-end: geocode -> OSM -> graph -> OpenDRIVE -> validate."""
    print("\n[13] Live OSM integration test (Bengaluru, 500m radius)")
    start = time.perf_counter()

    # 1. Geocode
    t0 = time.perf_counter()
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    t1 = time.perf_counter()
    check(resolution is not None, f"Geocode succeeded ({(t1-t0)*1000:.1f}ms)")
    if resolution is None:
        return
    lat = resolution.latitude
    lon = resolution.longitude
    print(f"    lat={lat}, lon={lon}, city={resolution.city}, country={resolution.country}")

    # 2. OSM download
    t0 = time.perf_counter()
    provider = OverpassProvider()
    raw = provider.download_radius(lat, lon, 500.0)
    t1 = time.perf_counter()
    check(raw is not None, f"OSM download succeeded ({(t1-t0)*1000:.1f}ms)")
    if raw is None:
        return
    osm_size = len(str(raw).encode("utf-8"))
    element_count = len(raw.get("elements", []))
    print(f"    OSM elements: {element_count}, size: {osm_size} bytes")

    roads = provider.fetch_roads()
    intersections = provider.fetch_intersections()
    print(f"    Roads: {len(roads)}, Intersections: {len(intersections)}")

    # 3. Graph
    t0 = time.perf_counter()
    graph = build_graph_from_osm(roads, intersections)
    t1 = time.perf_counter()
    ghash = graph_hash(graph)
    print(f"    Graph: nodes={graph.node_count()}, edges={graph.edge_count()}, hash={ghash[:16]}... ({(t1-t0)*1000:.1f}ms)")

    # 4. Projection
    t0 = time.perf_counter()
    projected = project_graph(graph, lat, lon)
    t1 = time.perf_counter()
    print(f"    Projected {projected.node_count()} nodes ({(t1-t0)*1000:.1f}ms)")

    # 5. OpenDRIVE
    t0 = time.perf_counter()
    compiler = OpenDriveCompiler(projected)
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "phase13_map.xodr")
        meta = compiler.compile(out_path)
        t1 = time.perf_counter()
        print(f"    OpenDRIVE: path={out_path}, size={meta['xodr_size_bytes']} bytes, fallbacks={len(meta.get('fallbacks', []))} ({(t1-t0)*1000:.1f}ms)")

        # 6. Validate
        t0 = time.perf_counter()
        validator = OpenDriveValidator()
        vresult = validator.validate(out_path)
        t1 = time.perf_counter()
        print(f"    Validator: valid={vresult['valid']}, errors={len(vresult['errors'])}, warnings={len(vresult['warnings'])} ({(t1-t0)*1000:.1f}ms)")
        print(f"    Stats: {vresult['statistics']}")

    total_ms = (time.perf_counter() - start) * 1000.0
    print(f"    TOTAL: {total_ms:.1f} ms")

    check(element_count > 0, "OSM elements > 0")
    check(len(roads) > 0, "Roads > 0")
    check(graph.node_count() > 0, "Graph nodes > 0")
    check(graph.edge_count() > 0, "Graph edges > 0")
    check(meta['xodr_size_bytes'] > 0, "OpenDRIVE file non-empty")
    check(vresult['valid'] is True, "OpenDRIVE validates")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 13 - Live OSM Integration Test")
    print("=" * 65)

    try:
        test_13_live_integration()
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
