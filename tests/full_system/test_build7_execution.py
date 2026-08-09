"""
Full System Acceptance Test — Step 5: Build 7 Execution Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests

API_BASE = "http://localhost:8000"

print("=" * 65)
print("  STEP 5 — Build 7: Execution Engine")
print("=" * 65)

try:
    resp = requests.post(f"{API_BASE}/execution/start", json={
        "world_plan_id": "world_acceptance_001",
        "seeds": {
            "master_seed": 42,
            "traffic_seed": 43,
            "spawn_seed": 44,
            "event_seed": 45,
            "weather_seed": 46,
            "sensor_seed": 47,
        },
    }, timeout=30)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    session_id = data.get("session_id")
    checks.append(("session_id present", session_id is not None and len(str(session_id)) > 0))
    
    status = data.get("status", "")
    checks.append(("status is READY or RUNNING", status in ["READY", "RUNNING"]))
    
    preflight = data.get("preflight", {})
    checks.append(("preflight passed", preflight.get("passed", False) is True))
    
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
        print("  BUILD 7 RESULT: PASS")
    else:
        print("  BUILD 7 RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  BUILD 7 RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
