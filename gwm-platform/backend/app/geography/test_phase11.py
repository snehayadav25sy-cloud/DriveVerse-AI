"""
Phase 11 tests — API endpoints

Run:
    python gwm-platform/backend/app/geography/test_phase11.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import requests

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


BASE_URL = "http://127.0.0.1:8000"


def test_11_1_resolve_valid():
    """11.1 POST /geography/resolve with valid location."""
    print("\n[11.1] POST /geography/resolve valid location")
    payload = {"location": "MG Road, Bengaluru", "radius_m": 1000}
    print(f"    Request: {payload}")
    resp = requests.post(f"{BASE_URL}/geography/resolve", json=payload, timeout=30)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response: {data}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check(data.get("status") == "resolved", "Status is resolved")
    check(data.get("resolution") is not None, "Resolution present")
    check(data.get("error") is None, "No error")


def test_11_2_build_valid():
    """11.2 POST /geography/build with valid location."""
    print("\n[11.2] POST /geography/build valid location")
    payload = {"location": "MG Road, Bengaluru", "radius_m": 1000}
    print(f"    Request: {payload}")
    resp = requests.post(f"{BASE_URL}/geography/build", json=payload, timeout=120)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Status: {data.get('status')}")
    print(f"    Stages: {list(data.get('stages', {}).keys())}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check(data.get("status") in ("complete", "completed_with_errors"), f"Build status: {data.get('status')}")
    check(data.get("map_artifact") is not None, "Map artifact present")
    check(data.get("provenance") is not None, "Provenance present")
    if data.get("error"):
        print(f"    Error: {data['error']}")


def test_11_3_resolve_bad_location():
    """11.3 POST /geography/resolve with bad location."""
    print("\n[11.3] POST /geography/resolve bad location")
    payload = {"location": "asdkjaslkdj123", "radius_m": 1000}
    print(f"    Request: {payload}")
    resp = requests.post(f"{BASE_URL}/geography/resolve", json=payload, timeout=30)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response: {data}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check(data.get("status") == "failed", "Status is failed for bad location")
    check(data.get("error") is not None, "Error message present")


def test_11_4_build_bad_location():
    """11.4 POST /geography/build with bad location."""
    print("\n[11.4] POST /geography/build bad location")
    payload = {"location": "asdkjaslkdj123", "radius_m": 1000}
    print(f"    Request: {payload}")
    resp = requests.post(f"{BASE_URL}/geography/build", json=payload, timeout=120)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response: {data}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check(data.get("status") == "failed", "Status is failed for bad location")
    check(data.get("error") is not None, "Error message present")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 11 - API Endpoint Tests")
    print("=" * 65)

    try:
        test_11_1_resolve_valid()
        test_11_2_build_valid()
        test_11_3_resolve_bad_location()
        test_11_4_build_bad_location()
    except AssertionError:
        pass
    except requests.exceptions.ConnectionError as e:
        print(f"\n[FAIL]  Cannot connect to backend at {BASE_URL}: {e}")
        print("       Start backend with: cd gwm-platform/backend && python main.py")
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
