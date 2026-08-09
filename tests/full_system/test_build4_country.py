"""
Full System Acceptance Test — Step 2: Build 4 Country Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests

API_BASE = "http://localhost:8000"

print("=" * 65)
print("  STEP 2 — Build 4: Country Engine")
print("=" * 65)

try:
    resp = requests.get(f"{API_BASE}/countries/resolve?country=India", timeout=30)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    rules = data.get("rules", {})
    drive_side = rules.get("drive_side", "")
    checks.append(("drive_side=left", drive_side == "left"))
    
    vehicle_mix = data.get("vehicle_mix", {})
    checks.append(("motorcycle in mix", "motorcycle" in str(vehicle_mix).lower()))
    
    behavior = rules.get("behavior", {})
    checks.append(("behavior params present", bool(behavior)))
    
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
        print("  BUILD 4 RESULT: PASS")
    else:
        print("  BUILD 4 RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  BUILD 4 RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
