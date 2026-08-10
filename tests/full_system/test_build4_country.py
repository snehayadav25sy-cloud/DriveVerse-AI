"""
Full System Acceptance Test — Step 2: Build 4 Country Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests
import pytest

API_BASE = "http://localhost:8000"


def get_auth_token():
    register_resp = requests.post(f"{API_BASE}/auth/register", json={
        "email": "acceptance_test4@example.com",
        "password": "testpass123"
    }, timeout=10)
    if register_resp.status_code not in (200, 201):
        login_resp = requests.post(f"{API_BASE}/auth/login", json={
            "email": "acceptance_test4@example.com",
            "password": "testpass123"
        }, timeout=10)
        data = login_resp.json()
        return data["access_token"]
    else:
        login_resp = requests.post(f"{API_BASE}/auth/login", json={
            "email": "acceptance_test4@example.com",
            "password": "testpass123"
        }, timeout=10)
        data = login_resp.json()
        return data["access_token"]


def test_build4_country_engine():
    print("=" * 65)
    print("  STEP 2 — Build 4: Country Engine")
    print("=" * 65)

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = requests.get(f"{API_BASE}/countries/India", headers=headers, timeout=30)
    print(f"HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}"
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    rules = data.get("rules", {})
    drive_side = rules.get("drive_side", "")
    assert drive_side == "left", f"drive_side={drive_side}"
    
    vehicle_mix = data.get("vehicle_mix", {})
    assert "motorcycle" in str(vehicle_mix).lower(), f"vehicle_mix={vehicle_mix}"
    
    behavior = rules.get("behavior", {})
    assert len(behavior) > 0, f"behavior={behavior}"
    
    print("\n" + "=" * 65)
    print("  BUILD 4 RESULT: PASS")
    print("=" * 65)
