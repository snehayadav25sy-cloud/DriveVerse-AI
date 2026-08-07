"""
Phase 14 tests — API endpoints
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_14_1_post_world_plan():
    payload = {
        "resolved_scenario": {"country": "usa", "weather": "sunny", "traffic": "normal"},
        "map_artifact": {"location_query": "test", "resolution": {"resolved_latitude": 0, "resolved_longitude": 0}, "carla_map_name": "Town01"},
        "country_profile": {"id": "usa", "rules": {"drive_side": "right"}},
    }
    resp = client.post("/world/plan", json=payload)
    check(resp.status_code == 200, f"POST /world/plan: {resp.status_code}")
    data = resp.json()
    check("world_id" in data, "Response has world_id")
    check("plan" in data, "Response has plan")
    check("provenance" in data, "Response has provenance")
    return data["world_id"]

def test_14_2_get_world(world_id):
    resp = client.get(f"/world/{world_id}")
    check(resp.status_code == 200, f"GET /world/{world_id}: {resp.status_code}")

def test_14_3_get_world_plan(world_id):
    resp = client.get(f"/world/{world_id}/plan")
    check(resp.status_code == 200, f"GET /world/{world_id}/plan: {resp.status_code}")

def test_14_4_get_world_provenance(world_id):
    resp = client.get(f"/world/{world_id}/provenance")
    check(resp.status_code == 200, f"GET /world/{world_id}/provenance: {resp.status_code}")

def test_14_5_get_world_artifacts(world_id):
    resp = client.get(f"/world/{world_id}/artifacts")
    check(resp.status_code == 200, f"GET /world/{world_id}/artifacts: {resp.status_code}")
    data = resp.json()
    check("buildings" in data, "Artifacts has buildings count")

def test_14_6_validate_world_plan():
    payload = {
        "resolved_scenario": {"country": "usa", "weather": "sunny", "traffic": "normal"},
        "map_artifact": {"location_query": "test", "resolution": {"resolved_latitude": 0, "resolved_longitude": 0}, "carla_map_name": "Town01"},
        "country_profile": {"id": "usa", "rules": {"drive_side": "right"}},
    }
    resp = client.post("/world/validate", json=payload)
    check(resp.status_code == 200, f"POST /world/validate: {resp.status_code}")
    data = resp.json()
    check(data.get("valid") is True, "Validation returned valid=True")

def test_14_7_get_nonexistent_world():
    resp = client.get("/world/nonexistent_id_xyz")
    check(resp.status_code == 404, f"GET /world/nonexistent: {resp.status_code}")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 14 - API Tests")
    print("=" * 65)
    world_id = None
    try:
        world_id = test_14_1_post_world_plan()
        test_14_2_get_world(world_id)
        test_14_3_get_world_plan(world_id)
        test_14_4_get_world_provenance(world_id)
        test_14_5_get_world_artifacts(world_id)
        test_14_6_validate_world_plan()
        test_14_7_get_nonexistent_world()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

