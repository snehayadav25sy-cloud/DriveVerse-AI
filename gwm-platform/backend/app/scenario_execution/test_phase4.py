"""
Phase 4 tests — Event scheduler
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.events.event_scheduler import EventScheduler

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_4_1_deterministic_schedule():
    scheduler1 = EventScheduler(master_seed=42, event_seed=100)
    scheduler2 = EventScheduler(master_seed=42, event_seed=100)
    events = [
        {"event_id": "e1", "event_type": "VEHICLE_BRAKING", "start_time_s": 5.0, "duration_s": 3.0},
        {"event_id": "e2", "event_type": "PEDESTRIAN_CROSSING", "start_time_s": 10.0, "duration_s": 5.0},
    ]
    schedule1 = scheduler1.schedule(events, 30.0)
    schedule2 = scheduler2.schedule(events, 30.0)
    check(len(schedule1) == 2, "Two events scheduled")
    check(schedule1[0].event_id == schedule2[0].event_id, "Deterministic event order")
    check(schedule1[0].start_time_s == schedule2[0].start_time_s, "Deterministic event times")

def test_4_2_different_seed():
    scheduler1 = EventScheduler(master_seed=42, event_seed=100)
    scheduler2 = EventScheduler(master_seed=42, event_seed=200)
    events = [
        {"event_id": "e1", "event_type": "VEHICLE_BRAKING", "start_time_s": 5.0, "duration_s": 3.0},
    ]
    schedule1 = scheduler1.schedule(events, 30.0)
    schedule2 = scheduler2.schedule(events, 30.0)
    check(schedule1[0].seed != schedule2[0].seed, "Different seeds produce different event seeds")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 4 - Event Scheduler Tests")
    print("=" * 65)
    try:
        test_4_1_deterministic_schedule()
        test_4_2_different_seed()
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
