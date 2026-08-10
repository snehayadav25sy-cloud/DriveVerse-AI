"""
Cross-build integration test: Build 5 → Build 6 → Build 7 data flow.
Verifies that no information is silently dropped between pipeline stages.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import hashlib
import requests
import pytest

API_BASE = "http://localhost:8000"


def test_build5_to_build6_to_build7_integration():
    """Verify that scenario, geography, and profile data propagate through the pipeline."""
    
    build5_payload = {
        "location": "MG Road, Bengaluru, India",
        "radius_m": 500.0,
    }
    geo_resp = requests.post(f"{API_BASE}/geography/build", json=build5_payload, timeout=180)
    assert geo_resp.status_code == 200, f"Build 5 failed: {geo_resp.text}"
    geo_data = geo_resp.json()
    
    map_artifact = geo_data["map_artifact"]
    resolve = geo_data["stages"]["resolve"]
    
    build6_payload = {
        "resolved_scenario": {
            "country": resolve.get("country", "India"),
            "city": resolve.get("city", "Bengaluru"),
            "location_query": map_artifact.get("location_query", "MG Road, Bengaluru, India"),
            "weather": "Rain",
            "traffic_density": "Heavy",
            "time_of_day": "Evening",
            "road_type": "City",
            "sensors": ["rgb", "lidar"],
            "frames": 20,
            "export_format": "kitti",
        },
        "map_artifact": {
            "provider": "opendrive_artifact",
            "map_name": map_artifact.get("carla_map_name") or "Town01",
            "xodr_path": map_artifact["xodr_path"],
            "xodr_hash": map_artifact["xodr_hash"],
            "location_query": map_artifact.get("location_query"),
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
    world_resp = requests.post(f"{API_BASE}/world/plan", json=build6_payload, timeout=120)
    assert world_resp.status_code == 200, f"Build 6 failed: {world_resp.text}"
    world_data = world_resp.json()
    world_plan_id = world_data["world_id"]
    
    build7_payload = {
        "world_plan_id": world_plan_id,
        "seeds": {
            "master_seed": 42,
            "traffic_seed": 43,
            "spawn_seed": 44,
            "event_seed": 45,
            "weather_seed": 46,
            "sensor_seed": 47,
        },
        "resolved_scenario": build6_payload["resolved_scenario"],
        "map_artifact": build6_payload["map_artifact"],
        "country_profile": build6_payload["country_profile"],
    }
    exec_resp = requests.post(f"{API_BASE}/execution/start", json=build7_payload, timeout=30)
    assert exec_resp.status_code == 200, f"Build 7 failed: {exec_resp.text}"
    exec_data = exec_resp.json()
    
    assert exec_data["status"] in ["READY", "RUNNING"]
    assert exec_data["preflight"]["passed"] is True
    
    session_id = exec_data["session_id"]
    status_resp = requests.get(f"{API_BASE}/execution/{session_id}/status", timeout=10)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["seeds"]["traffic_seed"] == 43
    assert status_data["map"]["map_name"] == "Town01"
