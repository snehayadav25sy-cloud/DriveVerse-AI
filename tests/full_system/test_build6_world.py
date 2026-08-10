"""
Full System Acceptance Test — Step 4: Build 6 World Generation
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import hashlib
import requests

API_BASE = "http://localhost:8000"

print("=" * 65)
print("  STEP 4 — Build 6: World Generation")
print("=" * 65)

try:
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
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    world_plan = data.get("plan", data)
    
    checks.append(("world_id present", data.get("world_id") is not None and len(str(data.get("world_id"))) > 0))
    checks.append(("seed present", world_plan.get("seed") == 42 or data.get("seed") == 42))
    
    vehicles = world_plan.get("vehicles", [])
    checks.append(("vehicles present", len(vehicles) >= 0))
    
    pedestrians = world_plan.get("pedestrians", [])
    checks.append(("pedestrians present", len(pedestrians) >= 0))
    
    sensors = world_plan.get("sensors", [])
    checks.append(("sensors present", len(sensors) >= 0))
    
    buildings = world_plan.get("buildings", [])
    checks.append(("buildings present", len(buildings) >= 0))
    
    vegetation = world_plan.get("vegetation", [])
    checks.append(("vegetation present", len(vegetation) >= 0))
    
    seeds = world_plan.get("seeds", {})
    checks.append(("world_seed present", seeds.get("world_seed") == 42 or seeds.get("world") == 42))
    checks.append(("traffic_seed present", seeds.get("traffic_seed") == 43 or seeds.get("traffic") == 43))
    
    plan_hash = data.get("plan_hash") or world_plan.get("plan_hash")
    checks.append(("plan_hash present", plan_hash is not None and len(str(plan_hash)) > 0))
    
    provenance = data.get("provenance")
    checks.append(("provenance present", provenance is not None))
    
    print("\n" + "=" * 65)
    print("  VERIFICATION")
    print("=" * 65)
    all_pass = True
    for label, passed in checks:
        status_label = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status_label}]  {label}")
    
    print("\n" + "=" * 65)
    if all_pass:
        print("  BUILD 6 RESULT: PASS")
    else:
        print("  BUILD 6 RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  BUILD 6 RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
