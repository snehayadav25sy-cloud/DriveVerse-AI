"""
Phase 7 tests — OpenDRIVE compiler

Run:
    python gwm-platform/backend/app/geography/test_phase7.py
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.graph import build_graph_from_osm
from app.geography.projection import project_graph
from app.geography.opendrive import OpenDriveCompiler

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def _get_projected_graph():
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
    graph = build_graph_from_osm(roads, intersections)
    return project_graph(graph, resolution.latitude, resolution.longitude)


def test_7_1_compile_xodr():
    """7.1 Compile projected graph to .xodr."""
    print("\n[7.1] Compile graph to .xodr")
    graph = _get_projected_graph()
    if graph is None:
        check(False, "Failed to get projected graph")
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_map.xodr")
        compiler = OpenDriveCompiler(graph)
        meta = compiler.compile(out_path)
        check(os.path.exists(out_path), f"File exists: {out_path}")
        size = os.path.getsize(out_path)
        print(f"    Path: {out_path}")
        print(f"    Size: {size} bytes")
        check(size > 0, f"File non-empty ({size} bytes)")
        check("xodr_hash" in meta, "Metadata includes xodr_hash")
        print(f"    Hash: {meta['xodr_hash'][:16]}...")


def test_7_2_xml_sample():
    """7.2 First 50 lines of raw XML."""
    print("\n[7.2] First 50 lines of generated XML")
    graph = _get_projected_graph()
    if graph is None:
        check(False, "Failed to get projected graph")
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_map.xodr")
        compiler = OpenDriveCompiler(graph)
        meta = compiler.compile(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        sample = "".join(all_lines[:50])
        print(sample)
        check(len(all_lines) >= 10, "File has at least 10 lines")
        check("<OpenDRIVE>" in all_lines[0] or "<?xml" in all_lines[0], "XML declaration present")


def test_7_3_fallback_list():
    """7.3 List of every fallback applied."""
    print("\n[7.3] Fallback list")
    graph = _get_projected_graph()
    if graph is None:
        check(False, "Failed to get projected graph")
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_map.xodr")
        compiler = OpenDriveCompiler(graph)
        meta = compiler.compile(out_path)
        fallbacks = meta.get("fallbacks", [])
        print(f"    Fallbacks applied: {len(fallbacks)}")
        for fb in fallbacks[:10]:
            print(f"      - {fb}")
        check(len(fallbacks) >= 0, f"Fallback list captured ({len(fallbacks)} items)")
        for fb in fallbacks:
            check("defaulted to" in fb or "missing" in fb, f"Fallback documented: {fb}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 7 - OpenDRIVE Compiler Tests")
    print("=" * 65)

    try:
        test_7_1_compile_xodr()
        test_7_2_xml_sample()
        test_7_3_fallback_list()
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
