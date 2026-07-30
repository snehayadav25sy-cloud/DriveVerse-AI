"""
prompt.py — Build 3: AI Prompt Engine v1.0 (COMPLETE)
=======================================================
Endpoints:
  POST /prompt/parse       — prompt → ScenarioConfig (dry run, no job)
  POST /prompt/generate    — prompt → parse → validate → submit real job
  POST /prompt/refine      — refine an existing scenario (additive, context-aware)
  GET  /prompt/history     — prompt history for current user
  GET  /prompt/provider    — active LLM provider info
"""
import sys
import os
from pathlib import Path

# Make prompt-engine importable from backend
_engine_root = Path(__file__).parent.parent.parent.parent.parent / "prompt-engine"
if str(_engine_root) not in sys.path:
    sys.path.insert(0, str(_engine_root))

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import json
import uuid

from app.database.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.job import Job
from app.models.prompt import Prompt as PromptModel, Scenario as ScenarioModel, Revision

router = APIRouter(prefix="/prompt", tags=["prompt"])


# ── Request / Response models ─────────────────────────────────────────────────

class PromptParseRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)


class RefineRequest(BaseModel):
    scenario_id: str
    refinement:  str = Field(..., min_length=1, max_length=2000)


class GenerateRequest(BaseModel):
    prompt:     str = Field(..., min_length=1, max_length=2000)
    project_id: str


# ── Helper: import lazily (prompt-engine may not be on PYTHONPATH at import) ──

def _get_parser():
    from parser.parser import parse_prompt
    return parse_prompt

def _get_validator():
    from validators.validator import validate_scenario
    return validate_scenario

def _get_llm_client():
    from llm.client import get_client
    return get_client()


# ── POST /prompt/parse ────────────────────────────────────────────────────────

@router.post("/parse")
def parse_scenario_prompt(
    body: PromptParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Parse a natural-language scenario description.
    Returns validated ScenarioConfig JSON + validation results.
    Raises 422 if prompt is ambiguous/non-scenario.
    Raises 502 if LLM call fails.
    """
    try:
        parse_prompt = _get_parser()
        cfg = parse_prompt(body.prompt)
    except ValueError as exc:
        # Insufficient information — return clarification questions
        raise HTTPException(
            status_code=422,
            detail={"error": "insufficient_information", "message": str(exc)}
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "llm_failure", "message": str(exc)}
        )

    # Run plausibility validator
    validate = _get_validator()
    vresult = validate(cfg, source_prompt=body.prompt)

    # Build response
    scenario_dict = cfg.dict()
    scenario_dict["validation"] = {
        "passed": vresult.passed,
        "errors": vresult.errors,
        "warnings": vresult.warnings,
    }

    return scenario_dict


# ── POST /prompt/generate ──────────────────────────────────────────────────────

@router.post("/generate")
def generate_from_prompt(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Full pipeline: prompt → parse → validate → submit real job.
    Returns job_id + parsed scenario.
    Rejects with 422 if validation fails.
    """
    # Ownership check
    project = db.query(Project).filter(
        Project.id == body.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Parse
    try:
        parse_prompt = _get_parser()
        cfg = parse_prompt(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "insufficient_information", "message": str(exc)})
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"error": "llm_failure", "message": str(exc)})

    # Validate
    validate = _get_validator()
    vresult = validate(cfg, source_prompt=body.prompt)
    if not vresult.passed:
        raise HTTPException(
            status_code=422,
            detail={"error": "validation_failed", "errors": vresult.errors}
        )

    # Save prompt + scenario to DB
    prompt_row = PromptModel(
        id=str(uuid.uuid4()), user_id=current_user.id,
        project_id=body.project_id, text=body.prompt,
    )
    db.add(prompt_row)

    scenario_row = ScenarioModel(
        id=str(uuid.uuid4()), prompt_id=prompt_row.id,
        scenario_json=cfg.dict(),
        llm_provider=cfg.llm_provider,
    )
    db.add(scenario_row)
    db.flush()

    # Submit job through existing /jobs pipeline
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

    # Create initial revision (version 1)
    rev = Revision(
        id=str(uuid.uuid4()), scenario_id=scenario_row.id,
        version=1, refinement=None, scenario_json=cfg.dict(),
    )
    db.add(rev)
    db.commit()
    db.refresh(job)

    return {
        "job_id":   job.id,
        "scenario": cfg.dict(),
        "scenario_id": scenario_row.id,
        "validation": {"passed": True, "warnings": vresult.warnings},
    }


# ── POST /prompt/refine ────────────────────────────────────────────────────────

@router.post("/refine")
def refine_scenario(
    body: RefineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Apply a refinement on top of an existing scenario, preserving history.
    Creates a new Revision row rather than overwriting prior state.
    """
    scenario_row = db.query(ScenarioModel).filter(
        ScenarioModel.id == body.scenario_id
    ).first()
    if not scenario_row:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Build context prompt: prior scenario JSON + refinement instruction
    prior_json = json.dumps(scenario_row.scenario_json, indent=2)
    combined_prompt = (
        f"The current scenario is:\n{prior_json}\n\n"
        f"Apply this refinement: {body.refinement}\n\n"
        f"Return the FULL updated scenario as JSON, preserving all prior fields "
        f"unless the refinement explicitly changes them."
    )

    try:
        parse_prompt = _get_parser()
        cfg = parse_prompt(combined_prompt)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail={"error": str(exc)})

    # Save new revision (additive)
    next_version = len(scenario_row.revisions) + 2  # version 1 is initial
    rev = Revision(
        id=str(uuid.uuid4()), scenario_id=scenario_row.id,
        version=next_version, refinement=body.refinement,
        scenario_json=cfg.dict(),
    )
    db.add(rev)

    # Update current scenario JSON on the scenario row
    scenario_row.scenario_json = cfg.dict()
    db.commit()

    return {
        "scenario_id": scenario_row.id,
        "version":     next_version,
        "scenario":    cfg.dict(),
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
            "id": p.id,
            "text": p.text,
            "created_at": p.created_at.isoformat(),
            "project_id": p.project_id,
            "scenario": None,
            "job_id": None,
        }
        if p.scenario:
            item["scenario"] = p.scenario.scenario_json
            item["job_id"]   = p.scenario.job_id
        result.append(item)
    return result


# ── GET /prompt/provider ───────────────────────────────────────────────────────

@router.get("/provider")
def get_provider(current_user: User = Depends(get_current_user)) -> Any:
    """Return active LLM provider info (name, capabilities)."""
    try:
        client = _get_llm_client()
        return {
            "provider": client.provider_name,
            "supports_refinement": True,
        }
    except Exception as exc:
        return {
            "provider": "unavailable",
            "error": str(exc),
            "supports_refinement": False,
        }


# ── GET /prompt/revisions/{scenario_id} ───────────────────────────────────────

@router.get("/revisions/{scenario_id}")
def get_revisions(
    scenario_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Return all revision history for a scenario."""
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
            "version":   r.version,
            "refinement": r.refinement,
            "scenario":  r.scenario_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in revisions
    ]
