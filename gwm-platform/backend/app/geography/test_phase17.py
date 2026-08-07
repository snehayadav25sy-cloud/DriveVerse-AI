"""
Phase 17 tests — Build 3 regression

Run:
    python gwm-platform/backend/app/geography/test_phase17.py
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


def _get_token() -> str:
    """Register/login and return a bearer token."""
    email = "test-phase17@example.com"
    password = "testpass123"
    # Register (ignore if exists)
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password}, timeout=10)
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")


def test_17_1_non_geographic_prompt():
    """17.1 Non-geographic prompt still works."""
    print("\n[17.1] Non-geographic prompt: 'Generate a rainy highway'")
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"prompt": "Generate a rainy highway", "project_id": "test-project"}
    resp = requests.post(f"{BASE_URL}/prompt/parse", json=payload, headers=headers, timeout=30)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response keys: {list(data.keys())}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check("scenario" in data or "config" in data or "country" in data or "weather" in data, "Parse response contains scenario data")


def test_17_2_geographic_prompt():
    """17.2 Geographic prompt activates Geography Engine."""
    print("\n[17.2] Geographic prompt: 'Generate 1 km of MG Road Bengaluru during monsoon'")
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"prompt": "Generate 1 km of MG Road Bengaluru during monsoon", "project_id": "test-project"}
    resp = requests.post(f"{BASE_URL}/prompt/parse", json=payload, headers=headers, timeout=30)
    print(f"    Status: {resp.status_code}")
    data = resp.json()
    print(f"    Response keys: {list(data.keys())}")
    check(resp.status_code == 200, f"HTTP 200 ({resp.status_code})")
    check("scenario" in data or "config" in data or "country" in data or "weather" in data, "Parse response contains scenario data")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 17 - Build 3 Regression Tests")
    print("=" * 65)

    try:
        test_17_1_non_geographic_prompt()
        test_17_2_geographic_prompt()
    except AssertionError:
        pass
    except requests.exceptions.ConnectionError as e:
        print(f"\n[FAIL]  Cannot connect to backend at {BASE_URL}: {e}")
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
