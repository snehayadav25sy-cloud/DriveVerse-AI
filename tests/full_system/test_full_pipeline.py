"""
Full System Acceptance Test — Complete Pipeline
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import requests

API_BASE = "http://localhost:8000"

PROMPT = "Generate a rainy monsoon evening driving scenario in Bengaluru, India around MG Road, with heavy traffic, motorcycles, cars, buses, pedestrians, RGB and LiDAR sensors, 20 frames, KITTI export."


def run_pipeline():
    print("=" * 65)
    print("  FULL SYSTEM PIPELINE TEST")
    print("=" * 65)
    print(f"\nSCENARIO: {PROMPT}\n")

    results = {}
    try:
        # Register test user
        reg = requests.post(f"{API_BASE}/auth/register", json={"email": "acceptance_test@test.com", "password": "testpass123"}, timeout=30)
        print(f"Register HTTP {reg.status_code}: {reg.text[:200]}")
        token = None
        if reg.status_code == 200:
            token = reg.json().get("access_token") or reg.json().get("token")
        if not token:
            login = requests.post(f"{API_BASE}/auth/login", json={"email": "acceptance_test@test.com", "password": "testpass123"}, timeout=30)
            print(f"Login HTTP {login.status_code}: {login.text[:200]}")
            token = login.json().get("access_token") or login.json().get("token")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # Step 1: Build 3 Prompt Engine
        print("\n" + "=" * 65)
        print("  STEP 1 — Build 3: Prompt Engine")
        print("=" * 65)
        resp = requests.post(f"{API_BASE}/prompt/parse", json={"prompt": PROMPT}, headers=headers, timeout=30)
        print(f"HTTP {resp.status_code}")
        scenario_data = resp.json()
        print(json.dumps(scenario_data, indent=2)[:2000])
        results["build3_prompt"] = {"status_code": resp.status_code, "data": scenario_data}
        
        # Step 2: Build 4 Country Engine
        print("\n" + "=" * 65)
        print("  STEP 2 — Build 4: Country Engine")
        print("=" * 65)
        country_resp = requests.get(f"{API_BASE}/countries/India", timeout=30)
        print(f"HTTP {country_resp.status_code}")
        country_data = country_resp.json()
        print(json.dumps(country_data, indent=2)[:2000])
        results["build4_country"] = {"status_code": country_resp.status_code, "data": country_data}
        
        # Step 3: Build 5 Geography Engine
        print("\n" + "=" * 65)
        print("  STEP 3 — Build 5: Geography Engine")
        print("=" * 65)
        geo_resp = requests.post(f"{API_BASE}/geography/resolve", json={"location": "MG Road, Bengaluru, India"}, timeout=60)
        print(f"HTTP {geo_resp.status_code}")
        geo_data = geo_resp.json()
        print(json.dumps(geo_data, indent=2)[:2000])
        results["build5_geography"] = {"status_code": geo_resp.status_code, "data": geo_data}
        
        # Step 4: Build 6 World Generation
        print("\n" + "=" * 65)
        print("  STEP 4 — Build 6: World Generation")
        print("=" * 65)
        world_payload = {
            "resolved_scenario": {"country": "India", "weather": "Rain", "traffic_density": "Heavy"},
            "map_artifact": {"provider": "town", "map_name": "Town01"},
            "country_profile": {"id": "india", "rules": {"drive_side": "left"}},
            "seeds": {"world_seed": 42, "traffic_seed": 43, "spawn_seed": 44, "weather_seed": 45, "sensor_seed": 46},
        }
        world_resp = requests.post(f"{API_BASE}/world/plan", json=world_payload, timeout=60)
        print(f"HTTP {world_resp.status_code}")
        world_data = world_resp.json()
        print(json.dumps(world_data, indent=2)[:2000])
        results["build6_world"] = {"status_code": world_resp.status_code, "data": world_data}
        
        # Step 5: Build 7 Execution Engine
        print("\n" + "=" * 65)
        print("  STEP 5 — Build 7: Execution Engine")
        print("=" * 65)
        world_plan_id = world_data.get("world_id") if world_resp.status_code == 200 else None
        exec_resp = requests.post(f"{API_BASE}/execution/start", json={"world_plan_id": world_plan_id or "test"}, timeout=30)
        print(f"HTTP {exec_resp.status_code}")
        exec_data = exec_resp.json()
        print(json.dumps(exec_data, indent=2)[:2000])
        results["build7_execution"] = {"status_code": exec_resp.status_code, "data": exec_data}
        
        # Save pipeline result
        with open("tests/full_system/pipeline_result.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print("\nPipeline result saved to tests/full_system/pipeline_result.json")
        
    except Exception as e:
        print(f"PIPELINE ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
