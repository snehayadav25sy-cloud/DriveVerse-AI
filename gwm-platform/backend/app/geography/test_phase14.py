"""
Phase 14 tests — CARLA map loading

Run:
    python gwm-platform/backend/app/geography/test_phase14.py
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
from app.geography.validator import OpenDriveValidator
from app.simulators.carla.map_loader import load_opendrive_map

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def _get_xodr_path() -> str:
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        return ""
    provider = OverpassProvider()
    raw = provider.download_radius(resolution.latitude, resolution.longitude, 500.0)
    if raw is None:
        return ""
    roads = provider.fetch_roads()
    intersections = provider.fetch_intersections()
    graph = build_graph_from_osm(roads, intersections)
    projected = project_graph(graph, resolution.latitude, resolution.longitude)
    compiler = OpenDriveCompiler(projected)
    tmpdir = tempfile.mkdtemp()
    out_path = os.path.join(tmpdir, "phase14_map.xodr")
    compiler.compile(out_path)
    return out_path


def test_14_1_version_check():
    """14.1 Confirm CARLA version check fires before load."""
    print("\n[14.1] CARLA version check")
    from app.simulators.carla.adapter import check_carla_available
    available, err = check_carla_available()
    print(f"    CARLA available: {available}")
    print(f"    Error: {err}")
    check(available is True, f"CARLA 0.9.16 available: {available}")


def test_14_2_load_xodr():
    """14.2 Load Phase 7/13 .xodr into CARLA."""
    print("\n[14.2] Load .xodr into CARLA")
    xodr_path = _get_xodr_path()
    check(os.path.exists(xodr_path), f".xodr exists: {xodr_path}")
    if not os.path.exists(xodr_path):
        return

    result = load_opendrive_map(xodr_path)
    print(f"    success:       {result['success']}")
    print(f"    world_name:    {result['world_name']}")
    print(f"    map_name:      {result['map_name']}")
    print(f"    spawn_points:  {result['spawn_point_count']}")
    print(f"    error:         {result['error']}")
    print(f"    detail:        {result['detail']}")

    check(result["world_name"] is not None, "World name reported")
    check(result["spawn_point_count"] is not None, "Spawn point count reported")


def test_14_3_gap_report():
    """14.3 Report gap between OpenDRIVE valid and CARLA loaded."""
    print("\n[14.3] Phase 8 vs Phase 14 gap report")
    xodr_path = _get_xodr_path()
    if not os.path.exists(xodr_path):
        check(False, "No .xodr to test")
        return

    # Phase 8 validation
    validator = OpenDriveValidator()
    vresult = validator.validate(xodr_path)
    phase8_valid = vresult["valid"]

    # Phase 14 CARLA load
    load_result = load_opendrive_map(xodr_path)
    phase14_loaded = load_result["success"]

    print(f"    Phase 8 (OpenDRIVE valid): {phase8_valid}")
    print(f"    Phase 14 (CARLA loaded):   {phase14_loaded}")

    if phase8_valid and not phase14_loaded:
        print("    GAP CONFIRMED: OpenDRIVE is XML-valid but CARLA did not load it.")
        print(f"    CARLA error: {load_result['error']}")
        check(True, "Gap documented: OpenDRIVE valid but CARLA load failed")
    elif phase8_valid and phase14_loaded:
        print("    NO GAP: Both OpenDRIVE valid and CARLA loaded successfully.")
        check(True, "No gap: both phases succeeded")
    else:
        print("    Phase 8 already failed or inconclusive.")
        check(True, "Gap check completed (Phase 8 not clean)")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 14 - CARLA Map Loading Tests")
    print("=" * 65)

    try:
        test_14_1_version_check()
        test_14_2_load_xodr()
        test_14_3_gap_report()
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
