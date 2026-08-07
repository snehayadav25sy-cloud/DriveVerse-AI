"""
Phase 9 tests — Execution provenance
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.models import ExecutionSession, TimingConfig, ExecutionProvenance
from app.scenario_execution.provenance.execution_provenance import compute_execution_provenance

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_9_1_provenance_generation():
    session = ExecutionSession(
        session_id="s1",
        scenario_id="scenario_001",
        world_plan_id="world_001",
        seeds={"master_seed": 42, "traffic_seed": 43, "spawn_seed": 44, "event_seed": 45, "weather_seed": 46, "sensor_seed": 47},
    )
    resolved_scenario = {"country": "india", "weather": "rain"}
    class MockWorldPlan:
        def plan_hash(self):
            return "plan_hash_123"
    world_plan = MockWorldPlan()
    prov = compute_execution_provenance(session, resolved_scenario, world_plan)
    check(prov.session_id == "s1", "Session ID preserved")
    check(prov.master_seed == 42, "Master seed preserved")
    check(prov.provenance_hash() != "", "Provenance hash generated")

def test_9_2_deterministic_provenance():
    session1 = ExecutionSession(session_id="s1", seeds={"master_seed": 1, "traffic_seed": 2, "spawn_seed": 3, "event_seed": 4, "weather_seed": 5, "sensor_seed": 6})
    session2 = ExecutionSession(session_id="s1", seeds={"master_seed": 1, "traffic_seed": 2, "spawn_seed": 3, "event_seed": 4, "weather_seed": 5, "sensor_seed": 6})
    resolved = {"country": "usa"}
    class MockWorldPlan:
        def plan_hash(self):
            return "hash"
    prov1 = compute_execution_provenance(session1, resolved, MockWorldPlan())
    prov2 = compute_execution_provenance(session2, resolved, MockWorldPlan())
    check(prov1.provenance_hash() == prov2.provenance_hash(), "Deterministic provenance hash")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 9 - Provenance Tests")
    print("=" * 65)
    try:
        test_9_1_provenance_generation()
        test_9_2_deterministic_provenance()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
