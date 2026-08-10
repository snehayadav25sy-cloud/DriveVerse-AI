"""
Full System Acceptance Test — Step 5: Build 7 Execution Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests

API_BASE = "http://localhost:8000"


def test_build7_execution_engine():
    print("=" * 65)
    print("  STEP 5 — Build 7: Execution Engine")
    print("=" * 65)

    # First, create a world plan to use as input
    world_payload = {
        "resolved_scenario": {
            "country": "India",
            "city": "Bengaluru",
            "location_query": "MG Road, Bengaluru, India",
            "weather": "Rain",
            "traffic_density": "Heavy",
            "time_of_day": "Evening",
            "road_type": "City",
        },
        "map_artifact": {
            "provider": "town",
            "map_name": "Town01",
        },
        "country_profile": {
            "id": "india",
            "rules": {"drive_side": "left"},
        },
        "seeds": {
            "world_seed": 42,
            "traffic_seed": 43,
            "spawn_seed": 44,
            "weather_seed": 45,
            "sensor_seed": 46,
        },
    }
    world_resp = requests.post(f"{API_BASE}/world/plan", json=world_payload, timeout=120)
    assert world_resp.status_code == 200, f"World plan failed: {world_resp.text}"
    world_data = world_resp.json()
    world_plan_id = world_data.get("world_id")
    print(f"Created world plan: {world_plan_id}")
    
    # Now start execution
    resp = requests.post(f"{API_BASE}/execution/start", json={
        "world_plan_id": world_plan_id,
        "seeds": {
            "master_seed": 42,
            "traffic_seed": 43,
            "spawn_seed": 44,
            "event_seed": 45,
            "weather_seed": 46,
            "sensor_seed": 47,
        },
        "resolved_scenario": {
            "country": "India",
            "city": "Bengaluru",
            "location_query": "MG Road, Bengaluru, India",
            "weather": "Rain",
            "traffic_density": "Heavy",
            "time_of_day": "Evening",
            "road_type": "City",
        },
        "map_artifact": {
            "provider": "town",
            "map_name": "Town01",
        },
        "country_profile": {
            "id": "india",
            "rules": {"drive_side": "left"},
        },
    }, timeout=30)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}: {resp.text}"
    
    session_id = data.get("session_id")
    assert session_id is not None and len(str(session_id)) > 0, "session_id missing"
    
    status = data.get("status", "")
    assert status in ["READY", "RUNNING"], f"status={status}"
    
    preflight = data.get("preflight", {})
    assert preflight.get("passed", False) is True, f"preflight failed: {preflight}"
    
    print("\n" + "=" * 65)
    print("  BUILD 7 RESULT: PASS")
    print("=" * 65)
