"""
app/scenario_execution/session.py — Build 7: Execution session factory
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from app.scenario_execution.models import (
    ExecutionSession,
    MapConfig,
    SessionStatus,
    TimingConfig,
)
from app.scenario_execution.state_machine import ExecutionStateMachine


def create_execution_session(
    scenario_id: Optional[str] = None,
    world_plan_id: Optional[str] = None,
    resolved_scenario: Optional[Dict[str, Any]] = None,
    world_plan: Optional[Any] = None,
    seeds: Optional[Dict[str, int]] = None,
    timing: Optional[TimingConfig] = None,
    map_config: Optional[MapConfig] = None,
) -> ExecutionSession:
    """Create a new execution session."""
    session_id = str(uuid.uuid4())
    default_seeds = {
        "master_seed": 42,
        "traffic_seed": 43,
        "spawn_seed": 44,
        "event_seed": 45,
        "weather_seed": 46,
        "sensor_seed": 47,
    }
    if seeds:
        default_seeds.update(seeds)

    return ExecutionSession(
        session_id=session_id,
        scenario_id=scenario_id,
        world_plan_id=world_plan_id,
        status=SessionStatus.CREATED,
        seeds=default_seeds,
        timing=timing or TimingConfig(),
        map=map_config or MapConfig(),
    )
