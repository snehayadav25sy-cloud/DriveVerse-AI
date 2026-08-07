"""
Phase 2 tests — State machine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.scenario_execution.state_machine import ExecutionStateMachine, InvalidStateTransition
from app.scenario_execution.models import SessionStatus

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_2_1_valid_transitions():
    sm = ExecutionStateMachine(SessionStatus.CREATED)
    sm.transition_to(SessionStatus.VALIDATING)
    check(sm.status == SessionStatus.VALIDATING, "CREATED -> VALIDATING")
    sm.transition_to(SessionStatus.DEPLOYING_MAP)
    check(sm.status == SessionStatus.DEPLOYING_MAP, "VALIDATING -> DEPLOYING_MAP")
    sm.transition_to(SessionStatus.READY)
    check(sm.status == SessionStatus.READY, "DEPLOYING_MAP -> READY")
    sm.transition_to(SessionStatus.STARTING)
    check(sm.status == SessionStatus.STARTING, "READY -> STARTING")
    sm.transition_to(SessionStatus.RUNNING)
    check(sm.status == SessionStatus.RUNNING, "STARTING -> RUNNING")
    sm.transition_to(SessionStatus.PAUSED)
    check(sm.status == SessionStatus.PAUSED, "RUNNING -> PAUSED")
    sm.transition_to(SessionStatus.RUNNING)
    check(sm.status == SessionStatus.RUNNING, "PAUSED -> RUNNING")
    sm.transition_to(SessionStatus.STOPPING)
    check(sm.status == SessionStatus.STOPPING, "RUNNING -> STOPPING")
    sm.transition_to(SessionStatus.FINALIZING)
    check(sm.status == SessionStatus.FINALIZING, "STOPPING -> FINALIZING")
    sm.transition_to(SessionStatus.COMPLETED)
    check(sm.status == SessionStatus.COMPLETED, "FINALIZING -> COMPLETED")

def test_2_2_invalid_transitions():
    sm = ExecutionStateMachine(SessionStatus.CREATED)
    try:
        sm.transition_to(SessionStatus.RUNNING)
        check(False, "Should reject CREATED -> RUNNING")
    except InvalidStateTransition:
        check(True, "Rejected CREATED -> RUNNING")

def test_2_3_terminal_states():
    sm = ExecutionStateMachine(SessionStatus.COMPLETED)
    check(sm.is_terminal() is True, "COMPLETED is terminal")
    sm2 = ExecutionStateMachine(SessionStatus.FAILED)
    check(sm2.is_terminal() is True, "FAILED is terminal")

def test_2_4_reset():
    sm = ExecutionStateMachine(SessionStatus.RUNNING)
    sm.reset()
    check(sm.status == SessionStatus.CREATED, "Reset to CREATED")
    check(sm.history == [SessionStatus.CREATED], "History reset")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 2 - State Machine Tests")
    print("=" * 65)
    try:
        test_2_1_valid_transitions()
        test_2_2_invalid_transitions()
        test_2_3_terminal_states()
        test_2_4_reset()
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
