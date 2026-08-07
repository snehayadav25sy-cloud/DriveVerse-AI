"""
prompt-engine/schemas/scenario_schema.py
=========================================
Build 3 — Phase 1: Canonical Scenario JSON Schema

This module re-exports the canonical ScenarioConfig and related models
from the backend schema (gwm-platform/backend/app/schemas/scenario.py)
to ensure a single source of truth across the entire project.

Nothing in this file defines new schema logic — it is a compatibility
re-export so that existing prompt-engine imports continue to work after
schema reconciliation.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend app package is importable from prompt-engine
_backend_root = Path(__file__).parent.parent.parent.parent / "gwm-platform" / "backend"
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.schemas.scenario import (
    ScenarioConfig,
    VehicleMix,
    ValidationIssue,
    ValidationResult,
    OptimizerChange,
    TranslationResult,
    SUPPORTED_MAPS,
    SUPPORTED_SENSORS,
    SUPPORTED_FORMATS,
    SUPPORTED_ROAD_TYPES,
    SUPPORTED_WEATHER,
    SUPPORTED_TIME_OF_DAY,
    SUPPORTED_TRAFFIC_DENSITY,
)

__all__ = [
    "ScenarioConfig",
    "VehicleMix",
    "ValidationIssue",
    "ValidationResult",
    "OptimizerChange",
    "TranslationResult",
    "SUPPORTED_MAPS",
    "SUPPORTED_SENSORS",
    "SUPPORTED_FORMATS",
    "SUPPORTED_ROAD_TYPES",
    "SUPPORTED_WEATHER",
    "SUPPORTED_TIME_OF_DAY",
    "SUPPORTED_TRAFFIC_DENSITY",
]
