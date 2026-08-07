"""
Phase 18 tests — Build 4 regression

Run:
    python gwm-platform/backend/app/geography/test_phase18.py
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
    email = "test-phase18@example.com"
    password = "testpass123"
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password}, timeout=10)
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")


def test_18_country_profiles():
    """18: Country profiles still load correctly."""
    print("\n[18] Country profiles regression")
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    for country_id in ["india", "usa", "japan", "dubai"]:
        resp = requests.get(f"{BASE_URL}/countries/{country_id}", headers=headers, timeout=30)
        print(f"    {country_id}: status={resp.status_code}")
        check(resp.status_code == 200, f"{country_id} profile loads (HTTP {resp.status_code})")
        data = resp.json()
        check("id" in data, f"{country_id} profile has 'id'")
        check("rules" in data and "drive_side" in data.get("rules", {}), f"{country_id} profile has 'rules.drive_side'")


def test_18_scenario_expand():
    """18: Scenario expand still works."""
    print("\n[18] Scenario expand regression")
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "country": "india",
        "weather": "monsoon",
        "traffic": "heavy",
        "time_of_day": "evening",
        "road_type": "urban",
        "modifiers": []
    }
    resp = requests.post(f"{BASE_URL}/countries/scenario/expand", json=payload, headers=headers, timeout=30)
    print(f"    Status: {resp.status_code}")
    check(resp.status_code == 200, f"Scenario expand HTTP 200 ({resp.status_code})")
    data = resp.json()
    check("resolved_scenario" in data, "Response has resolved_scenario")
    rs = data.get("resolved_scenario", {})
    check("drive_side" in rs, "Expanded scenario has drive_side")
    print(f"    drive_side: {rs.get('drive_side')}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 18 - Build 4 Regression Tests")
    print("=" * 65)

    try:
        test_18_country_profiles()
        test_18_scenario_expand()
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
