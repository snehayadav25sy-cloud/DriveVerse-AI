"""
Phase 8 tests — OpenDRIVE validator

Run:
    python gwm-platform/backend/app/geography/test_phase8.py
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


def test_8_1_validate_clean_xodr():
    """8.1 Validate clean .xodr from Phase 7."""
    print("\n[8.1] Validate clean .xodr")
    graph = _get_projected_graph()
    if graph is None:
        check(False, "Failed to get projected graph")
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "clean.xodr")
        compiler = OpenDriveCompiler(graph)
        compiler.compile(out_path)
        validator = OpenDriveValidator()
        result = validator.validate(out_path)
        print(f"    valid:   {result['valid']}")
        print(f"    errors:  {len(result['errors'])}")
        print(f"    warnings:{len(result['warnings'])}")
        print(f"    stats:   {result['statistics']}")
        check(result["valid"] is True, "Clean .xodr is valid")
        check(len(result["errors"]) == 0, "Zero errors in clean .xodr")


def test_8_2_validate_corrupt_xodr():
    """8.2 Corrupt .xodr and confirm validator catches it."""
    print("\n[8.2] Validate corrupted .xodr")
    graph = _get_projected_graph()
    if graph is None:
        check(False, "Failed to get projected graph")
        return
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "corrupt.xodr")
        compiler = OpenDriveCompiler(graph)
        compiler.compile(out_path)

        # Corrupt: duplicate a road ID and inject NaN
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Duplicate first road ID
        lines = content.splitlines()
        if len(lines) > 5:
            lines[5] = lines[4]  # duplicate the second road line
        # Inject NaN in geometry
        content = "\n".join(lines)
        content = content.replace('x="0.0"', 'x="NaN"', 1)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        validator = OpenDriveValidator()
        result = validator.validate(out_path)
        print(f"    valid:   {result['valid']}")
        print(f"    errors:  {len(result['errors'])}")
        for err in result["errors"][:5]:
            print(f"      - {err}")
        check(result["valid"] is False, "Corrupted .xodr is invalid")
        check(len(result["errors"]) > 0, "At least one error detected in corrupted .xodr")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 8 - OpenDRIVE Validator Tests")
    print("=" * 65)

    try:
        test_8_1_validate_clean_xodr()
        test_8_2_validate_corrupt_xodr()
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
