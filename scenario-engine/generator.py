"""
scenario-engine/generator.py
==============================
Build 3 — Phase 4: Scenario JSON → existing /jobs parameter bridge

Translates a validated ScenarioConfig into EXACTLY the parameters
the existing POST /jobs endpoint already accepts. This is a THIN
translation layer — it does NOT duplicate or fork any CARLA control
logic. All real CARLA execution continues through the existing
worker/simulator/carla/client.py path.
"""
from __future__ import annotations

import sys
import os
import logging
from pathlib import Path

# prompt-engine on path
sys.path.insert(0, str(Path(__file__).parent.parent / "prompt-engine"))

from schemas.scenario_schema import ScenarioConfig

log = logging.getLogger(__name__)


def scenario_to_job_params(cfg: ScenarioConfig) -> dict:
    """
    Produce the flat dict that POST /jobs accepts.

    Currently the /jobs endpoint accepts:
      project_id, map, sensors, frames, export_format
    (plus weather/traffic/pedestrians once the worker supports them).

    ONLY the fields the existing worker understands are included here.
    Additional Build 3 fields (weather intensity, etc.) are stored on the
    Scenario table and will be forwarded as the worker API evolves.
    """
    params = cfg.to_job_params()   # base: map, sensors, frames, export_format
    log.info(f"scenario_to_job_params: {params}")
    return params


def build_job_payload(cfg: ScenarioConfig, project_id: str) -> dict:
    """Full payload for POST /jobs including project_id."""
    return {
        "project_id":    project_id,
        **scenario_to_job_params(cfg),
    }
