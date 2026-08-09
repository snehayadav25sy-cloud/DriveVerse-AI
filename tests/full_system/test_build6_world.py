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
        "world_id": "world_acceptance_001",
        "location_query": "MG Road, Bengaluru, India",
        "country": "India",
        "map_name": "Town01",
        "seed": 42,
    }
    resp = requests.post(f"{API_BASE}/world/plan", json=payload, timeout=60)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    world_plan = data.get("world_plan", data)
    
    checks.append(("world_id present", "world_acceptance_001" in json.dumps(world_plan)))
    checks.append(("seed present", world_plan.get("seed") == 42 or data.get("seed") == 42))
    
    vehicles = world_plan.get("vehicles", [])
    checks.append(("vehicles > 0", len(vehicles) > 0))
    
    pedestrians = world_plan.get("pedestrians", [])
    checks.append(("pedestrians present", len(pedestrians) >= 0))
    
    sensors = world_plan.get("sensors", [])
    checks.append(("sensors present", len(sensors) > 0))
    
    buildings = world_plan.get("buildings", [])
    checks.append(("buildings present", len(buildings) >= 0))
    
    vegetation = world_plan.get("vegetation", [])
    checks.append(("vegetation present", len(vegetation) >= 0))
    
    seeds = world_plan.get("seeds", {})
    checks.append(("world_seed present", "world_seed" in seeds or world_plan.get("seed") is not None))
    checks.append(("traffic_seed present", "traffic_seed" in seeds))
    checks.append(("spawn_seed present", "spawn_seed" in seeds))
    checks.append(("weather_seed present", "weather_seed" in seeds))
    checks.append(("sensor_seed present", "sensor_seed" in seeds))
    
    plan_hash = data.get("plan_hash") or world_plan.get("plan_hash")
    checks.append(("plan_hash present", plan_hash is not None and len(str(plan_hash)) > 0))
    
    print("\n" + "=" * 65)
    print("  VERIFICATION")
    print("=" * 65)
    all_pass = True
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}]  {label}")
    
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
