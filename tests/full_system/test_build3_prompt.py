"""
Full System Acceptance Test — Step 1: Build 3 Prompt Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests

API_BASE = "http://localhost:8000"

PROMPT = "Generate a rainy monsoon evening driving scenario in Bengaluru, India around MG Road, with heavy traffic, motorcycles, cars, buses, pedestrians, RGB and LiDAR sensors, 20 frames, KITTI export."

print("=" * 65)
print("  STEP 1 — Build 3: Prompt Engine")
print("=" * 65)
print(f"\nPROMPT: {PROMPT}\n")

try:
    payload = {
        "prompt": PROMPT,
        "user_id": "acceptance_test",
    }
    resp = requests.post(f"{API_BASE}/prompt/parse", json=payload, timeout=30)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    checks = []
    scenario = data.get("scenario", data)
    
    country = scenario.get("country", scenario.get("location", {}).get("country", ""))
    checks.append(("country=India", str(country).lower() == "india" or "india" in str(country).lower()))
    
    city = scenario.get("city", scenario.get("location", {}).get("city", ""))
    checks.append(("city=Bengaluru", "bengaluru" in str(city).lower() or "bangalore" in str(city).lower()))
    
    location = scenario.get("location", {})
    location_str = json.dumps(location) if isinstance(location, dict) else str(location)
    checks.append(("MG Road present", "mg road" in location_str.lower()))
    
    weather = scenario.get("weather", "")
    checks.append(("rain/monsoon", "rain" in str(weather).lower() or "monsoon" in str(weather).lower()))
    
    time_of_day = scenario.get("time_of_day", "")
    checks.append(("time=evening", "evening" in str(time_of_day).lower()))
    
    traffic = scenario.get("traffic_density", "")
    checks.append(("traffic=heavy", "heavy" in str(traffic).lower()))
    
    sensors = scenario.get("sensors", [])
    sensors_str = json.dumps(sensors) if isinstance(sensors, list) else str(sensors)
    checks.append(("sensors includes rgb", "rgb" in sensors_str.lower()))
    checks.append(("sensors includes lidar", "lidar" in sensors_str.lower()))
    
    frames = scenario.get("frames", 0)
    checks.append(("frames=20", int(frames) == 20))
    
    export_format = scenario.get("export_format", "")
    checks.append(("export_format=kitti", str(export_format).lower() == "kitti"))
    
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
        print("  BUILD 3 RESULT: PASS")
    else:
        print("  BUILD 3 RESULT: FAIL")
    print("=" * 65)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"ERROR: {e}")
    print("\n" + "=" * 65)
    print("  BUILD 3 RESULT: FAIL")
    print("=" * 65)
    sys.exit(1)
