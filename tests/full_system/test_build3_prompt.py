"""
Full System Acceptance Test — Step 1: Build 3 Prompt Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests
import pytest

API_BASE = "http://localhost:8000"

PROMPT = "Generate a rainy monsoon evening driving scenario in Bengaluru, India around MG Road, with heavy traffic, motorcycles, cars, buses, pedestrians, RGB and LiDAR sensors, 20 frames, KITTI export."


def get_auth_token():
    register_resp = requests.post(f"{API_BASE}/auth/register", json={
        "email": "acceptance_test@example.com",
        "password": "testpass123"
    }, timeout=10)
    if register_resp.status_code not in (200, 201):
        login_resp = requests.post(f"{API_BASE}/auth/login", json={
            "email": "acceptance_test@example.com",
            "password": "testpass123"
        }, timeout=10)
        data = login_resp.json()
        return data["access_token"]
    else:
        login_resp = requests.post(f"{API_BASE}/auth/login", json={
            "email": "acceptance_test@example.com",
            "password": "testpass123"
        }, timeout=10)
        data = login_resp.json()
        return data["access_token"]


def test_build3_prompt_engine():
    print("=" * 65)
    print("  STEP 1 — Build 3: Prompt Engine")
    print("=" * 65)
    print(f"\nPROMPT: {PROMPT}\n")

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "prompt": PROMPT,
    }
    resp = requests.post(f"{API_BASE}/prompt/parse", json=payload, headers=headers, timeout=30)
    print(f"HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}"
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    scenario = data.get("scenario", data)
    
    country = scenario.get("country", scenario.get("location", {}).get("country", ""))
    assert str(country).lower() == "india" or "india" in str(country).lower(), f"country={country}"
    
    city = scenario.get("city", scenario.get("location", {}).get("city", ""))
    assert "bengaluru" in str(city).lower() or "bangalore" in str(city).lower(), f"city={city}"
    
    location_query = scenario.get("location_query", scenario.get("location", ""))
    location_str = str(location_query)
    assert "mg road" in location_str.lower(), f"location_query={location_query}"
    
    weather = scenario.get("weather", "")
    assert "rain" in str(weather).lower() or "monsoon" in str(weather).lower(), f"weather={weather}"
    
    time_of_day = scenario.get("time_of_day", "")
    assert "evening" in str(time_of_day).lower(), f"time_of_day={time_of_day}"
    
    traffic = scenario.get("traffic_density", "")
    assert "heavy" in str(traffic).lower(), f"traffic_density={traffic}"
    
    sensors = scenario.get("sensors", [])
    sensors_str = json.dumps(sensors) if isinstance(sensors, list) else str(sensors)
    assert "rgb" in sensors_str.lower(), f"sensors={sensors}"
    assert "lidar" in sensors_str.lower(), f"sensors={sensors}"
    
    frames = scenario.get("frames", 0)
    assert int(frames) == 20, f"frames={frames}"
    
    export_format = scenario.get("export_format", "")
    assert str(export_format).lower() == "kitti", f"export_format={export_format}"
    
    print("\n" + "=" * 65)
    print("  BUILD 3 RESULT: PASS")
    print("=" * 65)
