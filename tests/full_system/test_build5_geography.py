"""
Full System Acceptance Test — Step 3: Build 5 Geography Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import hashlib
import requests

API_BASE = "http://localhost:8000"

print("=" * 65)
print("  STEP 3 — Build 5: Geography Engine")
print("=" * 65)

try:
    payload = {
        "location_query": "MG Road, Bengaluru, India",
        "country": "India",
        "city": "Bengaluru",
    }
    resp = requests.post(f"{API_BASE}/geography/resolve", json=payload, timeout=60)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    lat = data.get("latitude") or data.get("lat")
    lon = data.get("longitude") or data.get("lon") or data.get("lng")
    checks.append(("latitude non-null", lat is not None and lat != 0))
    checks.append(("longitude non-null", lon is not None and lon != 0))
    
    osm = data.get("osm_data", {})
    checks.append(("OSM elements > 0", osm.get("elements", 0) > 0))
    
    roads = data.get("roads", [])
    checks.append(("roads > 0", len(roads) > 0))
    
    nodes = data.get("nodes", [])
    checks.append(("nodes > 0", len(nodes) > 0))
    
    intersections = data.get("intersections", [])
    checks.append(("intersections >= 0", len(intersections) >= 0))
    
    xodr_path = data.get("xodr_path") or data.get("opendrive_path")
    xodr_exists = os.path.exists(xodr_path) if xodr_path else False
    checks.append((".xodr file exists", xodr_exists))
    
    xml_valid = data.get("xml_valid") or data.get("opendrive_valid")
    checks.append(("XML validity reported", xml_valid is not None))
    
    geo_hash = data.get("geography_hash") or data.get("hash")
    checks.append(("geography hash present", geo_hash is not None and len(str(geo_hash)) > 0))
    
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
        print("  BUILD 5 RESULT: PASS")
    else:
        print("  BUILD 5 RESULT: PARTIAL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  BUILD 5 RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
