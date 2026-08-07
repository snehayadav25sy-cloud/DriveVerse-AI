"""
prompt.py — Build 3 v1.0 Stable: AI Prompt Engine API
=======================================================
Complete pipeline: prompt → parse → validate → optimize → translate → preview → job

Endpoints:
  POST /prompt/parse              — full pipeline dry-run (no job created)
  POST /prompt/generate           — full pipeline + create real job
  POST /prompt/optimize           — optimize an existing ScenarioConfig
  POST /prompt/preview            — estimate cost/time/disk for a ScenarioConfig
  POST /prompt/refine             — refine an existing scenario (additive revision)
  GET  /prompt/history            — prompt history for current user
  GET  /prompt/provider           — active LLM provider info
  GET  /prompt/maps               — city → CARLA map lookup table
  GET  /prompt/templates          — 10 built-in scenario templates
  GET  /prompt/revisions/{id}     — revision history for a scenario
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from sqlalchemy.orm import Session
import json
import uuid

from app.database.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.job import Job
from app.models.prompt import Prompt as PromptModel, Scenario as ScenarioModel, Revision
from app.schemas.scenario import ScenarioConfig, VehicleMix
from app.services.prompt_validator import validate_scenario
from app.services.prompt_optimizer import optimize_scenario
from app.services.scenario_translator import translate_scenario, ALL_MAP_ENTRIES
from app.services.scenario_estimator import estimate_scenario
from app.services.llm_providers.factory import get_provider, get_provider_info

router = APIRouter(prefix="/prompt", tags=["prompt"])


# ── Request / Response models ─────────────────────────────────────────────────

class PromptParseRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    project_id: str


class OptimizeRequest(BaseModel):
    scenario: dict  # raw ScenarioConfig dict


class PreviewRequest(BaseModel):
    scenario: dict  # raw ScenarioConfig dict


class RefineRequest(BaseModel):
    scenario_id: str
    refinement: str = Field(..., min_length=1, max_length=2000)


# ── Build 3.8 — Scenario Templates ────────────────────────────────────────────

SCENARIO_TEMPLATES: List[dict] = [
    {
        "id": "rain_city",
        "label": "🌧 Rain — City",
        "prompt": "Heavy rain in a busy city intersection at dusk, RGB and LiDAR, 500 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "Intersection", "weather": "Rain",
            "time_of_day": "Dusk", "traffic_density": "Heavy",
            "vehicles": {"car": 60, "truck": 10, "bus": 5, "motorcycle": 0, "bicycle": 0, "van": 0},
            "pedestrians": 40, "sensors": ["rgb", "lidar"], "frames": 500,
            "export_format": "kitti", "carla_map": "Town01",
        }
    },
    {
        "id": "fog_highway",
        "label": "🌫 Fog — Highway",
        "prompt": "Dense fog on a motorway at dawn with radar and LiDAR, 750 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "Highway", "weather": "Fog",
            "time_of_day": "Dawn", "traffic_density": "Medium",
            "vehicles": {"car": 80, "truck": 20, "bus": 0, "motorcycle": 0, "bicycle": 0, "van": 0},
            "pedestrians": 0, "sensors": ["rgb", "lidar", "radar"], "frames": 750,
            "export_format": "kitti", "carla_map": "Town03",
        }
    },
    {
        "id": "night_urban",
        "label": "🌙 Night — Urban",
        "prompt": "Night-time urban city with artificial lighting, full sensor suite, 1000 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "City", "weather": "Clear",
            "time_of_day": "Night", "lighting": "Artificial", "traffic_density": "Medium",
            "vehicles": {"car": 50, "truck": 5, "bus": 3, "motorcycle": 5, "bicycle": 0, "van": 0},
            "pedestrians": 30, "sensors": ["rgb", "lidar", "radar", "depth"], "frames": 1000,
            "export_format": "kitti", "carla_map": "Town01",
        }
    },
    {
        "id": "rush_hour",
        "label": "🚗 Rush Hour",
        "prompt": "Rush hour heavy traffic in a suburban area, RGB camera, 500 frames, COCO",
        "scenario": {
            "schema_version": "3.1", "road_type": "Suburban", "weather": "Clear",
            "time_of_day": "Day", "traffic_density": "Heavy",
            "vehicles": {"car": 150, "truck": 20, "bus": 8, "motorcycle": 10, "bicycle": 5, "van": 10},
            "pedestrians": 80, "sensors": ["rgb"], "frames": 500,
            "export_format": "coco", "carla_map": "Town02",
        }
    },
    {
        "id": "emergency",
        "label": "🚨 Emergency — Construction",
        "prompt": "Emergency vehicle routing through construction zone, depth camera + semantic, 300 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "City", "weather": "Overcast",
            "time_of_day": "Day", "traffic_density": "Light",
            "vehicles": {"car": 20, "truck": 5, "bus": 0, "motorcycle": 0, "bicycle": 0, "van": 5},
            "pedestrians": 15, "sensors": ["rgb", "depth", "semantic"], "frames": 300,
            "export_format": "kitti", "carla_map": "Town01",
        }
    },
    {
        "id": "school_zone",
        "label": "🏫 School Zone",
        "prompt": "School zone at 8am, many pedestrians and cyclists, slow traffic, RGB + instance segmentation",
        "scenario": {
            "schema_version": "3.1", "road_type": "Residential", "weather": "Clear",
            "time_of_day": "Day", "traffic_density": "Light",
            "vehicles": {"car": 30, "truck": 0, "bus": 2, "motorcycle": 0, "bicycle": 15, "van": 0},
            "pedestrians": 80, "sensors": ["rgb", "instance"], "frames": 400,
            "export_format": "kitti", "carla_map": "Town02",
        }
    },
    {
        "id": "mountain_rural",
        "label": "⛰ Mountain — Rural",
        "prompt": "Rural mountain road at dusk, light fog, RGB and radar, 600 frames, nuScenes",
        "scenario": {
            "schema_version": "3.1", "road_type": "Rural", "weather": "Fog",
            "time_of_day": "Dusk", "traffic_density": "Light",
            "vehicles": {"car": 15, "truck": 3, "bus": 0, "motorcycle": 2, "bicycle": 0, "van": 0},
            "pedestrians": 5, "sensors": ["rgb", "radar"], "frames": 600,
            "export_format": "nuscenes", "carla_map": "Town02",
        }
    },
    {
        "id": "airport",
        "label": "✈ Airport — Apron",
        "prompt": "Airport apron area with slow vehicle traffic, optical flow + depth, 200 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "Parking", "weather": "Clear",
            "time_of_day": "Day", "traffic_density": "Light",
            "vehicles": {"car": 10, "truck": 20, "bus": 3, "motorcycle": 0, "bicycle": 0, "van": 8},
            "pedestrians": 50, "sensors": ["rgb", "depth", "optical_flow"], "frames": 200,
            "export_format": "kitti", "carla_map": "Town01",
        }
    },
    {
        "id": "port",
        "label": "🚢 Port — Industrial",
        "prompt": "Industrial port with heavy truck traffic, semantic segmentation + LiDAR, 1000 frames",
        "scenario": {
            "schema_version": "3.1", "road_type": "City", "weather": "Overcast",
            "time_of_day": "Day", "traffic_density": "Heavy",
            "vehicles": {"car": 10, "truck": 80, "bus": 0, "motorcycle": 0, "bicycle": 0, "van": 20},
            "pedestrians": 30, "sensors": ["rgb", "lidar", "semantic"], "frames": 1000,
            "export_format": "kitti", "carla_map": "Town01",
        }
    },
    {
        "id": "snow_suburban",
        "label": "❄ Snow — Suburban",
        "prompt": "Snowy suburban neighbourhood at night, multimodal sensors, 800 frames, COCO",
        "scenario": {
            "schema_version": "3.1", "road_type": "Suburban", "weather": "Snow",
            "time_of_day": "Night", "lighting": "Artificial", "traffic_density": "Light",
            "vehicles": {"car": 20, "truck": 3, "bus": 0, "motorcycle": 0, "bicycle": 0, "van": 2},
            "pedestrians": 10, "sensors": ["rgb", "lidar", "radar"], "frames": 800,
            "export_format": "coco", "carla_map": "Town02",
        }
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_pipeline(prompt: str) -> tuple[ScenarioConfig, dict]:
    """
    Full Build 3 parse pipeline:
      parse → validate → optimize → translate

    Returns (ScenarioConfig, validation_dict).
    Raises HTTPException on parse failure.
    """
    provider = get_provider()
    try:
        cfg = provider.parse(prompt)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "insufficient_information", "message": str(exc)},
        )
    except (RuntimeError, NotImplementedError, EnvironmentError) as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "llm_failure", "message": str(exc)},
        )

    cfg.llm_provider = provider.name
    cfg.source_prompt = prompt

    # Validate
    vresult = validate_scenario(cfg)

    # Optimize (skip if LLM provider already produced rich config)
    if provider.supports_optimization:
        optimize_scenario(cfg)
        cfg.optimizer_applied = True

    # Translate → carla_map
    translate_scenario(cfg)

    validation_dict = {
        "passed":   vresult.passed,
        "errors":   [v.dict() for v in vresult.errors],
        "warnings": [v.dict() for v in vresult.warnings],
        "infos":    [v.dict() for v in vresult.infos],
    }
    return cfg, validation_dict


# ── POST /prompt/parse ────────────────────────────────────────────────────────

@router.post("/parse")
def parse_scenario_prompt(
    body: PromptParseRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Full pipeline dry-run. Returns ScenarioConfig + validation + optimizer changes
    + translation + preview estimate. No job is created.
    """
    cfg, validation_dict = _run_pipeline(body.prompt)

    # Add scenario estimate
    try:
        estimate = estimate_scenario(cfg)
        estimate_dict = estimate.dict()
    except Exception:
        estimate_dict = None

    result = cfg.dict()
    result["validation"] = validation_dict
    result["estimate"]   = estimate_dict
    return result


# ── POST /prompt/generate ──────────────────────────────────────────────────────

@router.post("/generate")
def generate_from_prompt(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Full pipeline + create real job.
    Rejects with 422 if validation returns errors.
    """
    project = db.query(Project).filter(
        Project.id == body.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cfg, validation_dict = _run_pipeline(body.prompt)

    if not validation_dict["passed"]:
        raise HTTPException(
            status_code=422,
            detail={"error": "validation_failed", "errors": validation_dict["errors"]},
        )

    # Persist prompt + scenario
    prompt_row = PromptModel(
        id=str(uuid.uuid4()), user_id=current_user.id,
        project_id=body.project_id, text=body.prompt,
    )
    db.add(prompt_row)

    scenario_row = ScenarioModel(
        id=str(uuid.uuid4()), prompt_id=prompt_row.id,
        scenario_json=cfg.dict(), llm_provider=cfg.llm_provider,
    )
    db.add(scenario_row)
    db.flush()

    # Submit job
    job_params = cfg.to_job_params()
    job = Job(
        id=str(uuid.uuid4()),
        project_id=body.project_id,
        map=job_params["map"],
        sensors=job_params["sensors"],
        frames=job_params["frames"],
        export_format=job_params["export_format"],
        status="queued",
    )
    db.add(job)
    scenario_row.job_id = job.id

    # Initial revision
    rev = Revision(
        id=str(uuid.uuid4()), scenario_id=scenario_row.id,
        version=1, refinement=None, scenario_json=cfg.dict(),
    )
    db.add(rev)
    db.commit()
    db.refresh(job)

    return {
        "job_id":      job.id,
        "scenario":    cfg.dict(),
        "scenario_id": scenario_row.id,
        "validation":  {"passed": True, "warnings": validation_dict["warnings"]},
    }


# ── POST /prompt/optimize ──────────────────────────────────────────────────────

@router.post("/optimize")
def optimize_endpoint(
    body: OptimizeRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Expand a ScenarioConfig with intelligent contextual defaults."""
    try:
        cfg = ScenarioConfig(**body.scenario)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    original = cfg.dict()
    optimize_scenario(cfg)
    translate_scenario(cfg)

    return {
        "original":        original,
        "optimized":       cfg.dict(),
        "changes_applied": [c.dict() for c in cfg.optimizer_changes],
        "expansion_summary": f"Applied {len(cfg.optimizer_changes)} optimization(s)",
    }


# ── POST /prompt/preview ──────────────────────────────────────────────────────

@router.post("/preview")
def preview_endpoint(
    body: PreviewRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Estimate capture time, disk usage, GPU VRAM for a ScenarioConfig."""
    try:
        cfg = ScenarioConfig(**body.scenario)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    estimate = estimate_scenario(cfg)
    return estimate.dict()


# ── POST /prompt/refine ────────────────────────────────────────────────────────

@router.post("/refine")
def refine_scenario(
    body: RefineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Apply a refinement on top of an existing scenario, preserving full revision history."""
    scenario_row = db.query(ScenarioModel).filter(
        ScenarioModel.id == body.scenario_id
    ).first()
    if not scenario_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    prior_json = json.dumps(scenario_row.scenario_json, indent=2)
    combined_prompt = (
        f"The current scenario is:\n{prior_json}\n\n"
        f"Apply this refinement: {body.refinement}\n\n"
        f"Return the FULL updated scenario as JSON, preserving all prior fields "
        f"unless the refinement explicitly changes them."
    )

    cfg, _ = _run_pipeline(combined_prompt)

    next_version = len(scenario_row.revisions) + 1
    rev = Revision(
        id=str(uuid.uuid4()), scenario_id=scenario_row.id,
        version=next_version, refinement=body.refinement,
        scenario_json=cfg.dict(),
    )
    db.add(rev)
    scenario_row.scenario_json = cfg.dict()
    db.commit()

    return {
        "scenario_id":    scenario_row.id,
        "version":        next_version,
        "scenario":       cfg.dict(),
        "revisions_count": next_version,
    }


# ── GET /prompt/history ────────────────────────────────────────────────────────

@router.get("/history")
def prompt_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return all prompt submissions for the current user, newest first."""
    prompts = (
        db.query(PromptModel)
        .filter(PromptModel.user_id == current_user.id)
        .order_by(PromptModel.created_at.desc())
        .all()
    )
    result = []
    for p in prompts:
        item = {
            "id":         p.id,
            "text":       p.text,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "project_id": p.project_id,
            "scenario":   None,
            "job_id":     None,
        }
        if p.scenario:
            item["scenario"] = p.scenario.scenario_json
            item["job_id"]   = p.scenario.job_id
        result.append(item)
    return result


# ── GET /prompt/provider ───────────────────────────────────────────────────────

@router.get("/provider")
def get_provider_endpoint(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return active LLM provider info."""
    return get_provider_info()


# ── GET /prompt/maps ──────────────────────────────────────────────────────────

@router.get("/maps")
def get_maps(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return the city → CARLA map lookup table."""
    return {
        "maps": ALL_MAP_ENTRIES,
        "total": len(ALL_MAP_ENTRIES),
    }


# ── GET /prompt/templates ─────────────────────────────────────────────────────

@router.get("/templates")
def get_templates(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return 10 built-in scenario templates for Build 3.8."""
    return {
        "templates": SCENARIO_TEMPLATES,
        "total":     len(SCENARIO_TEMPLATES),
    }


# ── GET /prompt/revisions/{scenario_id} ───────────────────────────────────────

@router.get("/revisions/{scenario_id}")
def get_revisions(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return full revision history for a scenario."""
    scenario_row = db.query(ScenarioModel).filter(
        ScenarioModel.id == scenario_id
    ).first()
    if not scenario_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    revisions = (
        db.query(Revision)
        .filter(Revision.scenario_id == scenario_id)
        .order_by(Revision.version)
        .all()
    )
    return [
        {
            "version":    r.version,
            "refinement": r.refinement,
            "scenario":   r.scenario_json,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in revisions
    ]
