"""
Phase 13 tests — World plan provenance
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.world_generation.models import WorldPlan, WorldCoordinate, WorldBoundingBox
from app.world_generation.provenance import compute_world_provenance, provenance_hash
from app.world_generation.planner import WorldPlanner

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_13_1_provenance_generation():
    prov = compute_world_provenance(
        build_version="6.0.0",
        country_profile_hash="abc123",
        geography_hash="def456",
        world_plan_hash="ghi789",
        asset_registry_hash="jkl012",
        seeds={"world": 1, "traffic": 2, "pedestrian": 3, "weather": 4, "asset": 5, "scenario": 6},
        git_commit="abc1234",
    )
    check(prov["build"] == "6.0.0", "Build version correct")
    check(prov["seeds"]["world"] == 1, "World seed correct")
    check(prov["seeds"]["traffic"] == 2, "Traffic seed correct")

def test_13_2_provenance_hash_determinism():
    prov1 = compute_world_provenance("6.0.0", "abc", "def", "ghi", "jkl", {"world": 1, "traffic": 2, "pedestrian": 3, "weather": 4, "asset": 5, "scenario": 6})
    prov2 = compute_world_provenance("6.0.0", "abc", "def", "ghi", "jkl", {"world": 1, "traffic": 2, "pedestrian": 3, "weather": 4, "asset": 5, "scenario": 6})
    h1 = provenance_hash(prov1)
    h2 = provenance_hash(prov2)
    check(h1 == h2, f"Deterministic provenance hash: {h1[:16]}...")

def test_13_3_full_chain():
    plan = WorldPlan(world_id="w1", seed=42, location_query="test", country="usa", map_name="Town01",
                     carla_coordinate_origin=WorldCoordinate(x=0, y=0, z=0),
                     bounding_box=WorldBoundingBox(min_x=-100, max_x=100, min_y=-100, max_y=100))
    planner = WorldPlanner({"traffic": "normal"}, {"location_query": "test", "resolution": {"resolved_latitude": 0, "resolved_longitude": 0}}, {"id": "usa"})
    p = planner.plan(seeds={"world": 42, "traffic": 43, "pedestrian": 44, "weather": 45, "asset": 46, "scenario": 47})
    prov = planner.provenance(p)
    check(prov.provenance_hash() != "", "Provenance hash generated")
    check(prov.world_plan_hash == p.plan_hash(), "World plan hash matches")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 13 - Provenance Tests")
    print("=" * 65)
    try:
        test_13_1_provenance_generation()
        test_13_2_provenance_hash_determinism()
        test_13_3_full_chain()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

