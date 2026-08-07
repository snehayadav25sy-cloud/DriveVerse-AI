"""
prompt-engine/parser/parser.py
===============================
Build 3 — Phase 2: Prompt → Scenario JSON parser

Sends prompt + structured template to LLM, parses + validates
the response against the canonical ScenarioConfig schema.

STRICT RULE: on LLM failure or unparseable/invalid output, raise —
never silently substitute a default or fabricated scenario.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Add prompt-engine root to path so relative imports work
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.client import get_client, _load_template
from schemas.scenario_schema import ScenarioConfig, VehicleMix

log = logging.getLogger(__name__)


def _derive_weather_label(weather_data: dict) -> str | None:
    """Derive a human-readable weather label from numeric intensities."""
    if not isinstance(weather_data, dict):
        return None
    rain = float(weather_data.get("rain", 0))
    fog = float(weather_data.get("fog", 0))
    cloudiness = float(weather_data.get("cloudiness", 0))
    if fog > 0.5:
        return "Fog"
    if rain > 0.8:
        return "Storm"
    if rain > 0.5:
        return "Rain"
    if cloudiness > 0.7:
        return "Overcast"
    if rain > 0.0 or fog > 0.0 or cloudiness > 0.0:
        return "Rain"
    return "Clear"


def _derive_traffic_density(traffic_data: dict) -> str | None:
    """Derive traffic density label from vehicle counts."""
    if not isinstance(traffic_data, dict):
        return None
    total = sum(int(traffic_data.get(k, 0)) for k in ("cars", "trucks", "buses", "motorcycles", "bicycles"))
    if total == 0:
        return "None"
    if total < 30:
        return "Light"
    if total < 100:
        return "Medium"
    if total < 250:
        return "Heavy"
    return "Gridlock"


def _normalize_legacy_format(data: dict) -> dict:
    """
    Transform legacy prompt-engine schema output to canonical backend schema.
    
    Legacy fields -> Canonical fields:
      map                -> carla_map
      weather {rain,...} -> weather (str label)
      traffic {cars...}  -> traffic_density (str) + vehicles (VehicleMix)
      road               -> road_type
    """
    normalized = dict(data)
    
    # map -> carla_map
    if "map" in normalized and "carla_map" not in normalized:
        normalized["carla_map"] = normalized.pop("map")
    
    # road -> road_type
    if "road" in normalized and "road_type" not in normalized:
        normalized["road_type"] = normalized.pop("road")
    
    # weather object -> weather string
    if isinstance(normalized.get("weather"), dict):
        normalized["weather"] = _derive_weather_label(normalized["weather"])
    
    # traffic object -> traffic_density + vehicles
    if isinstance(normalized.get("traffic"), dict):
        td = normalized.pop("traffic")
        normalized["traffic_density"] = _derive_traffic_density(td)
        normalized["vehicles"] = VehicleMix(
            car=int(td.get("cars", 0)),
            truck=int(td.get("trucks", 0)),
            bus=int(td.get("buses", 0)),
            motorcycle=int(td.get("motorcycles", 0)),
            bicycle=int(td.get("bicycles", 0)),
            van=0,
        )
    
    # Remove legacy keys that don't exist in backend schema
    for legacy_key in ("source_prompt", "llm_provider", "confidence", "schema_version"):
        normalized.pop(legacy_key, None)
    
    return normalized


def parse_prompt(prompt: str) -> ScenarioConfig:
    """
    Convert natural-language scenario description -> validated ScenarioConfig.

    Raises:
        ValueError  — if prompt contains no usable scenario information
        RuntimeError — if LLM call fails (network, auth, rate limit)
        ValidationError — if LLM output fails schema validation
    """
    system_prompt = _load_template()
    client = get_client()

    log.info(f"Parsing prompt via {client.provider_name}: {prompt[:80]!r}")

    # ── LLM call ──────────────────────────────────────────────────────────────
    try:
        raw = client.complete(user_prompt=prompt, system_prompt=system_prompt)
    except Exception as exc:
        raise RuntimeError(f"LLM call failed ({client.provider_name}): {exc}") from exc

    log.debug(f"Raw LLM output: {raw}")

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"LLM returned non-JSON output. "
            f"Raw (first 300 chars): {raw[:300]!r}. "
            f"Parse error: {exc}"
        ) from exc

    # ── Normalize legacy format (backward compat) ─────────────────────────────
    data = _normalize_legacy_format(data)

    # ── Insufficient-information check ────────────────────────────────────────
    # If the LLM signals no usable scenario info (carla_map is null / absent),
    # raise a clear ValueError instead of fabricating defaults.
    if data.get("carla_map") is None:
        clarifications = data.get("clarifications_needed", [])
        msg = (
            "Prompt contains insufficient information to generate a scenario. "
            + ("Questions: " + "; ".join(clarifications) if clarifications else "")
        )
        raise ValueError(msg)

    # Attach metadata
    data["source_prompt"] = prompt
    data["llm_provider"]  = client.provider_name

    # ── Schema validation ─────────────────────────────────────────────────────
    try:
        cfg = ScenarioConfig(**data)
    except (ValidationError, ValueError) as exc:
        raise RuntimeError(
            f"LLM output failed schema validation. "
            f"Error: {exc}. "
            f"Raw data: {json.dumps(data, default=str)[:500]}"
        ) from exc

    log.info(f"Parsed ScenarioConfig: carla_map={cfg.carla_map}, sensors={cfg.sensors}, frames={cfg.frames}")
    return cfg
