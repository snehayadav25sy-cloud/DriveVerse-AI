"""
app/scenario_execution/state_machine.py — Build 7: Session state machine

Valid state transitions:
  CREATED -> VALIDATING
  VALIDATING -> DEPLOYING_MAP | READY | FAILED
  DEPLOYING_MAP -> READY | FAILED
  READY -> STARTING | FAILED
  STARTING -> RUNNING | FAILED
  RUNNING -> PAUSED | STOPPING | FAILED
  PAUSED -> RUNNING | STOPPING | FAILED
  STOPPING -> FINALIZING | FAILED
  FINALIZING -> COMPLETED | FAILED
  Any -> CANCELLED (from non-terminal states)
  Any -> FAILED (from non-terminal states)
"""

from __future__ import annotations

from app.scenario_execution.models import SessionStatus


class InvalidStateTransition(Exception):
    """Raised when an illegal state transition is attempted."""


VALID_TRANSITIONS = {
    SessionStatus.CREATED: {SessionStatus.VALIDATING},
    SessionStatus.VALIDATING: {SessionStatus.DEPLOYING_MAP, SessionStatus.READY, SessionStatus.FAILED},
    SessionStatus.DEPLOYING_MAP: {SessionStatus.READY, SessionStatus.FAILED},
    SessionStatus.READY: {SessionStatus.STARTING, SessionStatus.FAILED},
    SessionStatus.STARTING: {SessionStatus.RUNNING, SessionStatus.FAILED},
    SessionStatus.RUNNING: {SessionStatus.PAUSED, SessionStatus.STOPPING, SessionStatus.FAILED},
    SessionStatus.PAUSED: {SessionStatus.RUNNING, SessionStatus.STOPPING, SessionStatus.FAILED},
    SessionStatus.STOPPING: {SessionStatus.FINALIZING, SessionStatus.FAILED},
    SessionStatus.FINALIZING: {SessionStatus.COMPLETED, SessionStatus.FAILED},
    SessionStatus.COMPLETED: set(),
    SessionStatus.FAILED: set(),
    SessionStatus.CANCELLED: set(),
}

TERMINAL_STATES = {
    SessionStatus.COMPLETED,
    SessionStatus.FAILED,
    SessionStatus.CANCELLED,
}


class ExecutionStateMachine:
    """Manages session state transitions."""

    def __init__(self, initial_status: SessionStatus = SessionStatus.CREATED):
        self._status = initial_status
        self._history: list[SessionStatus] = [initial_status]

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def history(self) -> list[SessionStatus]:
        return list(self._history)

    def can_transition_to(self, target: SessionStatus) -> bool:
        return target in VALID_TRANSITIONS.get(self._status, set())

    def transition_to(self, target: SessionStatus) -> None:
        if target == self._status:
            return
        if target not in VALID_TRANSITIONS.get(self._status, set()):
            raise InvalidStateTransition(
                f"Illegal transition: {self._status.value} -> {target.value}"
            )
        self._status = target
        self._history.append(target)

    def is_terminal(self) -> bool:
        return self._status in TERMINAL_STATES

    def reset(self) -> None:
        self._status = SessionStatus.CREATED
        self._history = [SessionStatus.CREATED]
