"""
prompt-engine/parser/parser.py
================================
Build 3 — Phase 2: Prompt → Scenario JSON parser

Sends prompt + structured template to LLM, parses + validates
the response against ScenarioConfig schema.

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
from schemas.scenario_schema import ScenarioConfig, SUPPORTED_MAPS

log = logging.getLogger(__name__)

# Fields that are nullable / may be null from LLM response
_NULLABLE_FIELDS = {"road", "country", "city", "time_of_day"}


def parse_prompt(prompt: str) -> ScenarioConfig:
    """
    Convert natural-language scenario description → validated ScenarioConfig.

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

    # ── Insufficient-information check ────────────────────────────────────────
    # If the LLM signals no usable scenario info (map is null / absent),
    # raise a clear ValueError instead of fabricating defaults.
    if data.get("map") is None:
        clarifications = data.get("clarifications_needed", [])
        msg = (
            "Prompt contains insufficient information to generate a scenario. "
            + ("Questions: " + "; ".join(clarifications) if clarifications else "")
        )
        raise ValueError(msg)

    # ── Normalize nested objects from LLM ────────────────────────────────────
    from schemas.scenario_schema import WeatherConfig, TrafficConfig

    if isinstance(data.get("weather"), dict):
        data["weather"] = WeatherConfig(**data["weather"])
    if isinstance(data.get("traffic"), dict):
        data["traffic"] = TrafficConfig(**data["traffic"])

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

    log.info(f"Parsed ScenarioConfig: map={cfg.map}, sensors={cfg.sensors}, frames={cfg.frames}")
    return cfg
