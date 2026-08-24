"""
app/api/world.py — Build 6: World generation REST API

Endpoints:
  POST /world/plan
  POST /world/validate
  POST /world/build
  GET /world/{world_id}
  GET /world/{world_id}/plan
  GET /world/{world_id}/provenance
  GET /world/{world_id}/artifacts
  POST /world/{world_id}/execute
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.world_generation.planner import WorldPlanner
from app.world_generation.models import WorldPlan, WorldProvenance
from app.world_generation.provenance import compute_world_provenance, provenance_hash

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/world", tags=["world"])

# In-memory storage for demo (replace with DB in production)
_world_store: Dict[str, Dict[str, Any]] = {}


class WorldPlanRequest(BaseModel):
    resolved_scenario: Dict[str, Any]
    map_artifact: Dict[str, Any]
    country_profile: Dict[str, Any]
    seeds: Optional[Dict[str, int]] = None


class WorldPlanResponse(BaseModel):
    world_id: str
    plan: Dict[str, Any]
    plan_hash: str
    provenance: Dict[str, Any]


@router.post("/plan", response_model=WorldPlanResponse)
async def create_world_plan(request: WorldPlanRequest):
    """
    Generate a deterministic world plan.
    Does NOT execute in CARLA.
    """
    try:
        planner = WorldPlanner(
            resolved_scenario=request.resolved_scenario,
            map_artifact=request.map_artifact,
            country_profile=request.country_profile,
        )
        plan = planner.plan(seeds=request.seeds)
        prov = planner.provenance(plan)

        world_id = plan.world_id
        _world_store[world_id] = {
            "plan": plan.model_dump(),
            "provenance": prov.model_dump(),
        }

        return WorldPlanResponse(
            world_id=world_id,
            plan=plan.model_dump(),
            plan_hash=plan.plan_hash(),
            provenance=prov.model_dump(),
        )
    except Exception as e:
        logger.error(f"World plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{world_id}", response_model=WorldPlanResponse)
async def get_world(world_id: str):
    if world_id not in _world_store:
        raise HTTPException(status_code=404, detail="World not found")
    entry = _world_store[world_id]
    return WorldPlanResponse(
        world_id=world_id,
        plan=entry["plan"],
        provenance=entry["provenance"],
    )


@router.get("/{world_id}/plan")
async def get_world_plan(world_id: str):
    if world_id not in _world_store:
        raise HTTPException(status_code=404, detail="World not found")
    return _world_store[world_id]["plan"]


@router.get("/{world_id}/provenance")
async def get_world_provenance(world_id: str):
    if world_id not in _world_store:
        raise HTTPException(status_code=404, detail="World not found")
    return _world_store[world_id]["provenance"]


@router.get("/{world_id}/artifacts")
async def get_world_artifacts(world_id: str):
    if world_id not in _world_store:
        raise HTTPException(status_code=404, detail="World not found")
    plan = _world_store[world_id]["plan"]
    return {
        "buildings": len(plan.get("buildings", [])),
        "vegetation": len(plan.get("vegetation", [])),
        "street_furniture": len(plan.get("street_furniture", [])),
        "signs": len(plan.get("signs", [])),
        "traffic_lights": len(plan.get("traffic_lights", [])),
        "vehicles": len(plan.get("vehicles", [])),
        "pedestrians": len(plan.get("pedestrians", [])),
        "events": len(plan.get("events", [])),
    }


@router.post("/validate")
async def validate_world_plan(request: WorldPlanRequest):
    """Validate inputs without generating a plan."""
    try:
        planner = WorldPlanner(
            resolved_scenario=request.resolved_scenario,
            map_artifact=request.map_artifact,
            country_profile=request.country_profile,
        )
        plan = planner.plan(seeds=request.seeds)
        prov = planner.provenance(plan)
        return {
            "valid": True,
            "world_id": plan.world_id,
            "plan_hash": plan.plan_hash(),
            "provenance_hash": prov.provenance_hash(),
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/{world_id}/execute")
async def execute_world_plan(world_id: str):
    """
    Execute a world plan in CARLA.
    Only available when CARLA is running.
    """
    if world_id not in _world_store:
        raise HTTPException(status_code=404, detail="World not found")

    try:
        from app.simulators.carla.adapter import connect, disconnect
        from app.simulators.carla.carla_world_executor import CarlaWorldExecutor
        from app.simulators.carla.map_provider import ExistingCarlaMapProvider, MapProviderState

        client, carla_world = connect()
        try:
            provider = ExistingCarlaMapProvider()
            provider.prepare({"carla_map_name": "Town01"})
            carla_world = provider.load(client)

            plan_data = _world_store[world_id]["plan"]
            plan = WorldPlan(**plan_data)
            executor = CarlaWorldExecutor(client, carla_world)
            report = executor.execute(plan)
            return report
        finally:
            disconnect(client, [])
    except Exception as e:
        logger.error(f"World execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
