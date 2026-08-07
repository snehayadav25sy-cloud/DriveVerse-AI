"""
Phase 4 tests — OSM cache

Run:
    python gwm-platform/backend/app/geography/test_phase4.py
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.cache import (
    compute_cache_key,
    cache_exists,
    read_cache,
    write_cache,
    list_cache_entries,
    GEOGRAPHY_CACHE_DIR,
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


def test_4_1_cache_hit():
    """4.1 Download same region twice — second hits cache."""
    print("\n[4.1] Cache hit on identical request")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    check(resolution is not None, "Geocode succeeded")
    if resolution is None:
        return
    lat = resolution.latitude
    lon = resolution.longitude

    provider = OverpassProvider()
    raw1 = provider.download_radius(lat, lon, 500.0)
    check(raw1 is not None, "First download succeeded")

    key = compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": 500.0})
    check(cache_exists(key), "Cache entry created after first download")

    # Second download — should hit cache
    raw2 = provider.download_radius(lat, lon, 500.0)
    check(raw2 is not None, "Second download succeeded")
    check(raw2 == raw1, "Second download returned identical data (cache hit)")

    entries = list_cache_entries()
    check(len(entries) >= 1, "At least one cache entry exists")
    print(f"    Cache entries: {len(entries)}")
    print(f"    Cache key:     {key[:16]}...")
    print(f"    Element count: {len(raw2.get('elements', []))}")


def test_4_2_different_radius():
    """4.2 Change radius 500m -> 600m — different cache key."""
    print("\n[4.2] Different radius creates different cache entry")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    if resolution is None:
        check(False, "Geocode failed")
        return
    lat = resolution.latitude
    lon = resolution.longitude

    key_500 = compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": 500.0})
    key_600 = compute_cache_key("overpass", {"lat": lat, "lon": lon, "radius_m": 600.0})

    check(key_500 != key_600, "Different radii produce different cache keys")

    provider = OverpassProvider()
    provider.download_radius(lat, lon, 500.0)
    provider.download_radius(lat, lon, 600.0)

    check(cache_exists(key_500), "500m cache entry exists")
    check(cache_exists(key_600), "600m cache entry exists")

    entries = list_cache_entries()
    keys = [e["cache_key"] for e in entries]
    check(key_500 in keys, "500m key found in cache listing")
    check(key_600 in keys, "600m key found in cache listing")
    print(f"    500m key: {key_500[:16]}...")
    print(f"    600m key: {key_600[:16]}...")
    print(f"    Total entries: {len(entries)}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 4 - OSM Cache Tests")
    print("=" * 65)

    # Clean cache before tests
    if os.path.exists(GEOGRAPHY_CACHE_DIR):
        shutil.rmtree(GEOGRAPHY_CACHE_DIR)

    try:
        test_4_1_cache_hit()
        test_4_2_different_radius()
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
