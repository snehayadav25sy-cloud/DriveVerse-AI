"""
app/api/execution.py — Build 7: Execution REST API
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.scenario_execution.orchestrator import ScenarioOrchestrator
from app.scenario_execution.models import ExecutionSession, MapConfig, SessionStatus, TimingConfig
from app.scenario_execution.state_machine import ExecutionStateMachine, InvalidStateTransition
from app.scenario_execution.preflight import PreflightValidator
from app.scenario_execution.provenance.execution_provenance import compute_execution_provenance
from app.world_generation.models import WorldCoordinate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/execution", tags=["execution"])

_orchestrator = ScenarioOrchestrator()
_sessions: Dict[str, ExecutionSession] = {}


class ExecutionStartRequest(BaseModel):
    world_plan_id: str
    seeds: Optional[Dict[str, int]] = None
    timing_override: Optional[Dict[str, float]] = None
    resolved_scenario: Optional[Dict[str, Any]] = None
    map_artifact: Optional[Dict[str, Any]] = None
    country_profile: Optional[Dict[str, Any]] = None


class ExecutionStartResponse(BaseModel):
    session_id: str
    status: str
    preflight: Dict[str, Any]


@router.post("/start", response_model=ExecutionStartResponse)
async def start_execution(request: ExecutionStartRequest):
    try:
        from app.world_generation.planner import WorldPlanner
        from app.world_generation.models import WorldPlan
        from app.api.world import _world_store

        if request.world_plan_id in _world_store:
            stored = _world_store[request.world_plan_id]
            world_plan = WorldPlan(**stored["plan"])
            resolved_scenario = stored["plan"].get("resolved_scenario", {"country": "usa", "weather": "sunny"})
        elif request.resolved_scenario and request.map_artifact and request.country_profile:
            planner = WorldPlanner(
                resolved_scenario=request.resolved_scenario,
                map_artifact=request.map_artifact,
                country_profile=request.country_profile,
            )
            world_plan = planner.plan(seeds=request.seeds)
            resolved_scenario = request.resolved_scenario
        else:
            world_plan = WorldPlan(
                world_id=request.world_plan_id,
                seed=42,
                location_query="test",
                country="usa",
                map_name="Town01",
                carla_coordinate_origin=WorldCoordinate(x=0.0, y=0.0, z=0.0),
            )
            resolved_scenario = {"country": "usa", "weather": "sunny"}

        session = _orchestrator.create_session(world_plan, resolved_scenario, request.seeds)

        if request.timing_override:
            session.timing = TimingConfig(**request.timing_override)

        session = _orchestrator.prepare_session(session, world_plan)
        preflight_report = _orchestrator.validate_session(session)

        if preflight_report.passed:
            session.status = SessionStatus.READY
        else:
            session.status = SessionStatus.FAILED

        _sessions[session.session_id] = session
        return ExecutionStartResponse(
            session_id=session.session_id,
            status=session.status.value,
            preflight=preflight_report.model_dump(),
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Execution start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_execution(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "current_frame": session.current_frame,
        "current_simulation_time_s": session.current_simulation_time_s,
        "actor_count": len(session.actors),
        "sensor_count": len(session.sensors),
        "event_count": len(session.events),
    }


@router.get("/{session_id}/status")
async def get_execution_status(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    return {
        "session_id": session.session_id,
        "status": session.status.value,
        "simulator": session.simulator,
        "map": session.map.model_dump(),
        "timing": session.timing.model_dump(),
        "seeds": session.seeds,
    }


@router.post("/{session_id}/stop")
async def stop_execution(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    sm = ExecutionStateMachine(session.status)
    try:
        sm.transition_to(SessionStatus.STOPPING)
        session.status = SessionStatus.STOPPING
        session.status = SessionStatus.FINALIZING
        session.status = SessionStatus.COMPLETED
        return {"session_id": session_id, "status": session.status.value}
    except InvalidStateTransition as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/events")
async def get_execution_events(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    return {"events": [e.model_dump() for e in session.events]}


@router.get("/{session_id}/validation")
async def get_execution_validation(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "validation": "pending"}


@router.get("/{session_id}/provenance")
async def get_execution_provenance(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    return {"session_id": session_id, "provenance": session.provenance}
