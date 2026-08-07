"""
app/world_generation/provenance.py — Build 6: World plan provenance utilities
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def compute_world_provenance(
    build_version: str,
    country_profile_hash: str,
    geography_hash: str,
    world_plan_hash: str,
    asset_registry_hash: str,
    seeds: Dict[str, int],
    git_commit: str = "unknown",
    carla_version: str = "0.9.16",
) -> Dict[str, Any]:
    """Build a provenance dict."""
    return {
        "build": build_version,
        "country_profile_hash": country_profile_hash,
        "geography_hash": geography_hash,
        "world_plan_hash": world_plan_hash,
        "asset_registry_hash": asset_registry_hash,
        "seeds": seeds,
        "git_commit": git_commit,
        "carla_version": carla_version,
        "schema_version": "1.0.0",
        "compiler_version": "1.0.0",
    }


def provenance_hash(provenance: Dict[str, Any]) -> str:
    raw = json.dumps(provenance, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
