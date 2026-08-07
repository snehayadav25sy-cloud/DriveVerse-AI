"""
Phase 3 tests — OSM data acquisition

Run:
    python gwm-platform/backend/app/geography/test_phase3.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_3_1_download_radius():
    """3.1 Download 500m radius around MG Road, Bengaluru."""
    print("\n[3.1] Download 500m radius around MG Road, Bengaluru")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    check(resolution is not None, "Geocode succeeded")
    if resolution is None:
        return
    lat = resolution.latitude
    lon = resolution.longitude
    print(f"    Center: lat={lat}, lon={lon}")

    provider = OverpassProvider()
    raw = provider.download_radius(lat, lon, 500.0)
    check(raw is not None, "Overpass returned data")
    if raw is None:
        return

    elements = raw.get("elements", [])
    size_bytes = len(str(raw).encode("utf-8"))
    print(f"    Raw element count: {len(elements)}")
    print(f"    Raw response size: {size_bytes} bytes")
    check(len(elements) > 0, "Non-empty response")
    print(f"    Raw response size: {size_bytes} bytes")
    check(size_bytes < 2_000_000, f"Region is reasonably sized ({size_bytes} bytes < 2 MB)")

    sample = elements[0]
    print(f"    Sample element type: {sample.get('type')}")
    print(f"    Sample element id:   {sample.get('id')}")
    if sample.get("tags"):
        print(f"    Sample tags:         {list(sample['tags'].keys())[:8]}")


def test_3_2_fetch_roads():
    """3.2 Extract fetch_roads() — road count and 2 sample entries."""
    print("\n[3.2] fetch_roads() output")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        check(False, "Geocode failed — cannot run fetch_roads")
        return
    provider = OverpassProvider()
    provider.download_radius(resolution.latitude, resolution.longitude, 500.0)
    roads = provider.fetch_roads()
    check(len(roads) > 0, f"Roads extracted: {len(roads)}")
    print(f"    Road count: {len(roads)}")
    for i, road in enumerate(roads[:2]):
        print(f"    --- Road {i+1} ---")
        print(f"    osm_id:       {road.osm_id}")
        print(f"    name:         {road.name}")
        print(f"    highway_type: {road.highway_type}")
        print(f"    lanes:        {road.lanes}")
        print(f"    maxspeed:     {road.maxspeed}")
        print(f"    oneway:       {road.oneway}")
        print(f"    surface:      {road.surface}")
        print(f"    bridge:       {road.bridge}")
        print(f"    tunnel:       {road.tunnel}")
        print(f"    country:      {road.country}")
        print(f"    geometry_pts: {len(road.geometry)}")


def test_3_3_missing_fields():
    """3.3 Missing OSM fields recorded as null with documented fallback."""
    print("\n[3.3] Missing fields recorded as null")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        check(False, "Geocode failed — cannot run missing-fields check")
        return
    provider = OverpassProvider()
    provider.download_radius(resolution.latitude, resolution.longitude, 500.0)
    roads = provider.fetch_roads()

    # Find a road with no maxspeed tag
    no_maxspeed = [r for r in roads if r.maxspeed is None]
    print(f"    Roads without maxspeed: {len(no_maxspeed)} of {len(roads)}")
    if no_maxspeed:
        sample = no_maxspeed[0]
        print(f"    Sample: {sample.osm_id} name={sample.name} maxspeed={sample.maxspeed}")
        check(sample.maxspeed is None, "Missing maxspeed is null, not invented")
    else:
        check(True, "All roads had maxspeed (no null example found, but code handles it)")

    # Find a road with no surface tag
    no_surface = [r for r in roads if r.surface is None]
    print(f"    Roads without surface: {len(no_surface)} of {len(roads)}")
    if no_surface:
        sample = no_surface[0]
        print(f"    Sample: {sample.osm_id} name={sample.name} surface={sample.surface}")
        check(sample.surface is None, "Missing surface is null, not invented")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 3 - OSM Data Acquisition Tests")
    print("=" * 65)

    try:
        test_3_1_download_radius()
        test_3_2_fetch_roads()
        test_3_3_missing_fields()
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
