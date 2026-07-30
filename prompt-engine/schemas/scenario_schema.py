"""
prompt-engine/schemas/scenario_schema.py
=========================================
Build 3 — Phase 1: Canonical Scenario JSON Schema

This is the single source of truth DSL for what a valid simulation
scenario looks like. It is a strict superset of the parameters the
existing /jobs endpoint already accepts (map, sensors, frames,
export_format) — extended with weather, traffic, road type, etc.

Nothing in this file touches CARLA directly. The Scenario Engine
(Phase 4) translates a validated ScenarioConfig into /jobs parameters.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


# ── Supported value sets (mirroring Build 2/2.1 worker constraints) ───────────

SUPPORTED_MAPS: frozenset[str] = frozenset({
    "Town01", "Town02", "Town03", "Town04", "Town05",
    "Town06", "Town07", "Town10HD",
})

SUPPORTED_SENSORS: frozenset[str] = frozenset({
    "rgb", "lidar", "radar", "depth",
    "semantic", "instance", "optical_flow",
})

SUPPORTED_FORMATS: frozenset[str] = frozenset({
    "internal", "kitti", "coco", "nuscenes",
})

SUPPORTED_ROAD_TYPES: frozenset[str] = frozenset({
    "highway", "urban", "rural", "mountain",
    "intersection", "residential", "parking",
    "bridge", "tunnel", "coastal",
})

SUPPORTED_WEATHER_CONDITIONS: frozenset[str] = frozenset({
    "clear", "rain", "fog", "snow", "storm",
    "overcast", "partly_cloudy", "dust",
})

SUPPORTED_TIME_OF_DAY: frozenset[str] = frozenset({
    "dawn", "morning", "noon", "afternoon",
    "dusk", "evening", "night", "midnight",
})

# Engine hard limits (from CARLA 0.9.16 tested constraints)
MAX_VEHICLES_TOTAL:   int = 500
MAX_PEDESTRIANS:      int = 200
MAX_FRAMES:           int = 2000
MIN_FRAMES:           int = 1
MAX_ACTIVE_SENSORS:   int = 7


# ── Sub-models ────────────────────────────────────────────────────────────────

class WeatherConfig(BaseModel):
    """CARLA uses 0.0–1.0 floats for weather intensity parameters."""
    rain:         float = Field(0.0, ge=0.0, le=1.0, description="Rain intensity")
    fog:          float = Field(0.0, ge=0.0, le=1.0, description="Fog density")
    cloudiness:   float = Field(0.0, ge=0.0, le=1.0, description="Cloud coverage")
    wind:         float = Field(0.0, ge=0.0, le=1.0, description="Wind intensity")
    wetness:      float = Field(0.0, ge=0.0, le=1.0, description="Road wetness")

    @validator("rain", "fog", "cloudiness", "wind", "wetness", pre=True)
    def clamp(cls, v):
        return max(0.0, min(1.0, float(v)))

    @property
    def label(self) -> str:
        """Human-readable weather label derived from intensity values."""
        if self.fog > 0.5:
            return "fog"
        if self.rain > 0.5:
            return "storm" if self.rain > 0.8 else "rain"
        if self.cloudiness > 0.7:
            return "overcast"
        return "clear"


class TrafficConfig(BaseModel):
    """Vehicle actor counts for the simulation scene."""
    cars:         int = Field(0, ge=0, description="Passenger cars")
    trucks:       int = Field(0, ge=0, description="Trucks / HGVs")
    buses:        int = Field(0, ge=0, description="Buses")
    motorcycles:  int = Field(0, ge=0, description="Motorcycles")
    bicycles:     int = Field(0, ge=0, description="Bicycles")

    @property
    def total(self) -> int:
        return self.cars + self.trucks + self.buses + self.motorcycles + self.bicycles


# ── Central contract ──────────────────────────────────────────────────────────

class ScenarioConfig(BaseModel):
    """
    Canonical Scenario JSON — the Build 3 DSL.

    Produced by the Prompt Engine and consumed by the Scenario Engine,
    which translates it into the exact parameters the existing /jobs
    endpoint already accepts.

    IMPORTANT: sensors and export_format MUST match the values the
    Build 2/2.1 worker already supports (see SUPPORTED_* sets above).
    """

    # ── Required ──────────────────────────────────────────────────────────────
    map:           str = Field(..., description="CARLA map name, e.g. Town01")
    sensors:       List[str] = Field(..., min_items=1, description="Active sensor suite")
    frames:        int = Field(..., ge=MIN_FRAMES, le=MAX_FRAMES)
    export_format: str = Field("kitti", description="Dataset export format")

    # ── Geography / road ─────────────────────────────────────────────────────
    country:       Optional[str] = None
    city:          Optional[str] = None
    road:          Optional[str] = Field(None, description="Road type enum")

    # ── Environment ───────────────────────────────────────────────────────────
    weather:       WeatherConfig = Field(default_factory=WeatherConfig)
    time_of_day:   Optional[str] = Field(None, description="HH:MM 24h or label")

    # ── Traffic ───────────────────────────────────────────────────────────────
    traffic:       TrafficConfig = Field(default_factory=TrafficConfig)
    pedestrians:   int = Field(0, ge=0)

    # ── Pipeline metadata (set by engine, not user) ───────────────────────────
    source_prompt:     Optional[str] = None
    llm_provider:      Optional[str] = None
    confidence:        Dict[str, float] = Field(default_factory=dict)
    clarifications_needed: List[str] = Field(default_factory=list)
    schema_version:    str = "3.1"

    # ── Validators ────────────────────────────────────────────────────────────

    @validator("map")
    def map_must_be_supported(cls, v):
        if v not in SUPPORTED_MAPS:
            raise ValueError(
                f"Unsupported map: '{v}'. Supported: {sorted(SUPPORTED_MAPS)}"
            )
        return v

    @validator("sensors", each_item=True)
    def sensors_must_be_supported(cls, v):
        if v not in SUPPORTED_SENSORS:
            raise ValueError(
                f"Unsupported sensor: '{v}'. Supported: {sorted(SUPPORTED_SENSORS)}"
            )
        return v

    @validator("sensors")
    def sensors_unique(cls, v):
        return list(dict.fromkeys(v))   # deduplicate preserving order

    @validator("export_format")
    def format_must_be_supported(cls, v):
        norm = v.lower().strip()
        if norm not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported export_format: '{v}'. Supported: {sorted(SUPPORTED_FORMATS)}"
            )
        return norm

    @validator("road")
    def road_must_be_supported(cls, v):
        if v is not None and v.lower() not in SUPPORTED_ROAD_TYPES:
            raise ValueError(
                f"Unsupported road type: '{v}'. Supported: {sorted(SUPPORTED_ROAD_TYPES)}"
            )
        return v.lower() if v else v

    def to_job_params(self) -> dict:
        """
        Extract the flat parameters that POST /jobs already accepts.
        This is the ONLY place that bridges Scenario JSON → Job API.
        """
        return {
            "map":           self.map,
            "sensors":       self.sensors,
            "frames":        self.frames,
            "export_format": self.export_format,
        }
