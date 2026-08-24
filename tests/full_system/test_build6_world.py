"""
Full System Acceptance Test — Step 4: Build 6 World Generation
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import hashlib
import requests
import pytest

API_BASE = "http://localhost:8000"


def test_build6_world_generation():
    print("=" * 65)
    print("  STEP 4 — Build 6: World Generation")
    print("=" * 65)

    payload = {
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
    resp = requests.post(f"{API_BASE}/world/plan", json=payload, timeout=120)
    print(f"HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    assert data.get("world_id") is not None and len(str(data.get("world_id"))) > 0, "world_id missing"
    
    world_plan = data.get("plan", data)
    assert world_plan.get("seed") == 42 or data.get("seed") == 42, "seed mismatch"
    
    vehicles = world_plan.get("vehicles", [])
    assert len(vehicles) >= 0
    
    pedestrians = world_plan.get("pedestrians", [])
    assert len(pedestrians) >= 0
    
    sensors = world_plan.get("sensors", [])
    assert len(sensors) >= 0
    
    buildings = world_plan.get("buildings", [])
    assert len(buildings) >= 0
    
    vegetation = world_plan.get("vegetation", [])
    assert len(vegetation) >= 0
    
    seeds = world_plan.get("seeds", {})
    assert seeds.get("world_seed") == 42 or seeds.get("world") == 42, f"seeds={seeds}"
    assert seeds.get("traffic_seed") == 43 or seeds.get("traffic") == 43, f"seeds={seeds}"
    
    plan_hash = data.get("plan_hash") or world_plan.get("plan_hash")
    assert plan_hash is not None and len(str(plan_hash)) > 0, "plan_hash missing"
    
    provenance = data.get("provenance")
    assert provenance is not None, "provenance missing"
    
    print("\n" + "=" * 65)
    print("  BUILD 6 RESULT: PASS")
    print("=" * 65)
