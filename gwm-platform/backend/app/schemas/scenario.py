"""
scenario.py — Build 3.1: Central Scenario JSON Contract
=========================================================
ScenarioConfig is the single source of truth that flows through:
  Prompt → Parse → Validate → Optimize → Translate → Preview → Job

Every API endpoint, worker, and frontend component speaks this schema.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


# ── Supported value sets ───────────────────────────────────────────────────────

SUPPORTED_MAPS: frozenset[str] = frozenset({
    "Town01", "Town02", "Town03",
    # Town04-Town07, Town10HD excluded: not produced by parser,
    # not confirmed loaded in this CARLA 0.9.16 installation.
    # Re-add here and in _MAP_ALIASES / VALID_MAPS when verified.
})

SUPPORTED_SENSORS: frozenset[str] = frozenset({
    "rgb", "lidar", "radar", "depth",
    "semantic", "instance", "optical_flow",
})

SUPPORTED_FORMATS: frozenset[str] = frozenset({
    "kitti", "coco", "nuscenes",
})

SUPPORTED_ROAD_TYPES: frozenset[str] = frozenset({
    "Highway", "City", "Rural", "Intersection", "Residential",
    "Suburban", "Parking",
})

SUPPORTED_WEATHER: frozenset[str] = frozenset({
    "Clear", "Rain", "Fog", "Snow", "Storm", "Overcast",
})

SUPPORTED_TIME_OF_DAY: frozenset[str] = frozenset({
    "Day", "Night", "Dusk", "Dawn",
})

SUPPORTED_TRAFFIC_DENSITY: frozenset[str] = frozenset({
    "None", "Light", "Medium", "Heavy", "Gridlock",
})


# ── Sub-models ────────────────────────────────────────────────────────────────

class VehicleMix(BaseModel):
    """Breakdown of vehicle actor counts for the simulation."""
    car:        int = Field(0, ge=0, description="Passenger cars")
    truck:      int = Field(0, ge=0, description="Trucks / HGVs")
    bus:        int = Field(0, ge=0, description="Buses")
    motorcycle: int = Field(0, ge=0, description="Motorcycles")
    bicycle:    int = Field(0, ge=0, description="Bicycles")
    van:        int = Field(0, ge=0, description="Vans / minivans")

    @property
    def total(self) -> int:
        return self.car + self.truck + self.bus + self.motorcycle + self.bicycle + self.van


class ValidationIssue(BaseModel):
    """A single validation error or warning."""
    level:   str   # "error" | "warning" | "info"
    field:   str   # e.g. "vehicles.total"
    message: str
    value:   Any = None
    limit:   Any = None


class ValidationResult(BaseModel):
    passed:   bool = True
    errors:   List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    infos:    List[ValidationIssue] = Field(default_factory=list)


class OptimizerChange(BaseModel):
    field:       str
    from_value:  Any = None
    to_value:    Any
    reason:      str


class TranslationResult(BaseModel):
    carla_map:  str
    confidence: float = 1.0   # 1.0 exact, 0.7 fallback, 0.3 default
    source:     str           # "city_lookup" | "road_type_fallback" | "default"
    note:       str = ""


# ── Core contract ─────────────────────────────────────────────────────────────

class ScenarioConfig(BaseModel):
    """
    The central Scenario JSON contract for DriveVerse AI.
    Produced by the Prompt Engine and consumed by the Job runner.
    """

    schema_version: str = "3.1"

    # ── Geography ──────────────────────────────────────────────────────────────
    country:  Optional[str] = None   # "Japan", "UAE", "UK" — Build 4 hook
    city:     Optional[str] = None   # "Tokyo", "Dubai", "London"
    road_type: Optional[str] = None  # "Highway" | "City" | "Rural" | "Intersection" | "Parking"
    modifiers: List[str] = Field(default_factory=list)

    # ── Environment ────────────────────────────────────────────────────────────
    weather:     Optional[str] = None  # "Clear" | "Rain" | "Fog" | "Snow" | "Storm" | "Overcast"
    time_of_day: Optional[str] = None  # "Day" | "Night" | "Dusk" | "Dawn"
    lighting:    Optional[str] = None  # "Default" | "Artificial" | "Overcast" | "Bright"

    # ── Traffic ────────────────────────────────────────────────────────────────
    traffic_density: Optional[str] = None  # "None" | "Light" | "Medium" | "Heavy" | "Gridlock"
    vehicles:   VehicleMix = Field(default_factory=VehicleMix)
    pedestrians: int = Field(0, ge=0)

    # ── Simulation ─────────────────────────────────────────────────────────────
    sensors:       List[str] = Field(default_factory=lambda: ["rgb"])
    frames:        int       = Field(500, ge=1, le=2000)
    export_format: str       = Field("kitti", pattern="^(kitti|coco|nuscenes)$")

    # ── Resolved by Translator (Build 3.7) ────────────────────────────────────
    carla_map: Optional[str] = None   # "Town01" | "Town02" | "Town03"

    # ── Engine metadata (set by pipeline, not by user) ─────────────────────────
    optimizer_applied:  bool = False
    validation_passed:  bool = False

    # ── Confidence scores (from parser) ───────────────────────────────────────
    confidence: Dict[str, float] = Field(default_factory=dict)
    explanation: List[str]       = Field(default_factory=list)
    unrecognised_tokens: List[str] = Field(default_factory=list)

    # ── LLM metadata ─────────────────────────────────────────────────────────
    source_prompt: Optional[str] = None
    llm_provider: Optional[str] = None

    # ── Pipeline results (attached by each stage) ─────────────────────────────
    validation:    Optional[ValidationResult]  = None
    optimizer_changes: List[OptimizerChange]   = Field(default_factory=list)
    translation:   Optional[TranslationResult] = None

    @validator("sensors", each_item=True)
    def sensors_must_be_supported(cls, v):
        if v not in SUPPORTED_SENSORS:
            raise ValueError(
                f"Unsupported sensor: '{v}'. Supported: {sorted(SUPPORTED_SENSORS)}"
            )
        return v

    @validator("sensors")
    def sensors_not_empty(cls, v):
        if not v:
            raise ValueError("sensors must contain at least one value")
        return list(dict.fromkeys(v))

    @validator("export_format", pre=True)
    def normalise_format(cls, v):
        return v.lower() if isinstance(v, str) else v

    @validator("carla_map")
    def carla_map_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_MAPS:
            raise ValueError(
                f"Unsupported carla_map: '{v}'. Supported: {sorted(SUPPORTED_MAPS)}"
            )
        return v

    @validator("road_type")
    def road_type_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_ROAD_TYPES:
            raise ValueError(
                f"Unsupported road_type: '{v}'. Supported: {sorted(SUPPORTED_ROAD_TYPES)}"
            )
        return v

    @validator("weather")
    def weather_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_WEATHER:
            raise ValueError(
                f"Unsupported weather: '{v}'. Supported: {sorted(SUPPORTED_WEATHER)}"
            )
        return v

    @validator("time_of_day")
    def time_of_day_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_TIME_OF_DAY:
            raise ValueError(
                f"Unsupported time_of_day: '{v}'. Supported: {sorted(SUPPORTED_TIME_OF_DAY)}"
            )
        return v

    @validator("traffic_density")
    def traffic_density_must_be_supported(cls, v):
        if v is not None and v not in SUPPORTED_TRAFFIC_DENSITY:
            raise ValueError(
                f"Unsupported traffic_density: '{v}'. Supported: {sorted(SUPPORTED_TRAFFIC_DENSITY)}"
            )
        return v

    def to_job_params(self) -> dict:
        """
        Extract the flat fields needed to create a Job record.
        Derives carla_map from translation if available.
        """
        return {
            "map":           self.carla_map or "Town01",
            "sensors":       self.sensors,
            "frames":        self.frames,
            "export_format": self.export_format,
        }
