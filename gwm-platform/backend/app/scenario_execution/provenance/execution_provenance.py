"""
app/scenario_execution/provenance/execution_provenance.py — Build 7: Execution provenance
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from app.scenario_execution.models import ExecutionProvenance


def compute_execution_provenance(
    session: Any,
    resolved_scenario: Dict[str, Any],
    world_plan: Any,
) -> ExecutionProvenance:
    """Build execution provenance from session, scenario, and world plan."""
    scenario_hash = hashlib.sha256(
        json.dumps(resolved_scenario, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]

    world_plan_hash = world_plan.plan_hash() if hasattr(world_plan, "plan_hash") else "unknown"

    provenance = ExecutionProvenance(
        session_id=session.session_id,
        scenario_id=session.scenario_id,
        world_plan_id=session.world_plan_id,
        scenario_hash=scenario_hash,
        world_plan_hash=world_plan_hash,
        master_seed=session.seeds.get("master_seed", 0),
        traffic_seed=session.seeds.get("traffic_seed", 0),
        spawn_seed=session.seeds.get("spawn_seed", 0),
        event_seed=session.seeds.get("event_seed", 0),
        weather_seed=session.seeds.get("weather_seed", 0),
        sensor_seed=session.seeds.get("sensor_seed", 0),
    )
    return provenance
