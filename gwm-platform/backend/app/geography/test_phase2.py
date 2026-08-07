"""
Phase 2 tests — Geocoder

Run:
    python gwm-platform/backend/app/geography/test_phase2.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.geocoder import NominatimGeocoder
from app.geography.models import LocationRequest

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_2_1_geocode_mg_road():
    """2.1 Geocode 'MG Road, Bengaluru'."""
    print("\n[2.1] Geocode 'MG Road, Bengaluru'")
    geocoder = NominatimGeocoder()
    result = geocoder.geocode("MG Road, Bengaluru")
    check(result is not None, "Geocoder returned a result")
    if result is None:
        check(False, "Result is None — cannot continue")
        return
    print(f"    latitude:      {result.latitude}")
    print(f"    longitude:     {result.longitude}")
    print(f"    display_name:  {result.display_name}")
    print(f"    country:       {result.country}")
    print(f"    country_code:  {result.country_code}")
    print(f"    state:         {result.state}")
    print(f"    city:          {result.city}")
    print(f"    bbox:          {result.bounding_box}")
    print(f"    provider:      {result.provider}")
    print(f"    timestamp:     {result.timestamp}")
    check(result.latitude is not None and result.longitude is not None, "Has lat/lon")
    check(result.country is not None, "Has country")
    check(result.provider == "nominatim", "Provider is nominatim")


def test_2_2_geocode_cache_hit():
    """2.2 Geocode same query again — cache hit."""
    print("\n[2.2] Cache hit on repeated query")
    geocoder = NominatimGeocoder()
    result1 = geocoder.geocode("MG Road, Bengaluru")
    check(result1 is not None, "First geocode succeeded")
    if result1 is None:
        return

    t0 = time.perf_counter()
    result2 = geocoder.geocode("MG Road, Bengaluru")
    t1 = time.perf_counter()
    elapsed_ms = (t1 - t0) * 1000.0

    check(result2 is not None, "Second geocode returned result")
    check(result2.cached is True, f"Cache hit flag is True (elapsed={elapsed_ms:.2f}ms)")
    check(elapsed_ms < 50, f"Cache hit was fast ({elapsed_ms:.2f}ms < 50ms)")


def test_2_3_reverse_geocode():
    """2.3 Reverse-geocode explicit coordinates."""
    print("\n[2.3] Reverse geocode 52.5200, 13.4050")
    geocoder = NominatimGeocoder()
    result = geocoder.reverse_geocode(52.5200, 13.4050)
    check(result is not None, "Reverse geocode returned a result")
    if result is None:
        check(False, "Result is None — cannot continue")
        return
    print(f"    latitude:      {result.latitude}")
    print(f"    longitude:     {result.longitude}")
    print(f"    display_name:  {result.display_name}")
    print(f"    country:       {result.country}")
    print(f"    city:          {result.city}")
    check(abs(result.latitude - 52.5200) < 0.01, "Latitude matches input")
    check(abs(result.longitude - 13.4050) < 0.01, "Longitude matches input")


def test_2_4_nonsense_query():
    """2.4 Geocode nonsense query — must fail honestly."""
    print("\n[2.4] Nonsense query 'asdkjaslkdj123'")
    geocoder = NominatimGeocoder()
    result = geocoder.geocode("asdkjaslkdj123")
    check(result is None, "Nonsense query returned None (no fabricated location)")
    print("    Result: None (correct — no fake location invented)")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 2 - Geocoder Tests")
    print("=" * 65)

    try:
        test_2_1_geocode_mg_road()
        test_2_2_geocode_cache_hit()
        test_2_3_reverse_geocode()
        test_2_4_nonsense_query()
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
