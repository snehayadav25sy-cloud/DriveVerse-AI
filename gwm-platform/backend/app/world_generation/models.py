"""
app/world_generation/models.py — Build 6: Procedural World Plan schema (Pydantic v2)

WorldPlan is the deterministic, inspectable, reproducible plan for a
simulation world. It is generated BEFORE any simulator execution.

Design:
  - No CARLA imports here.
  - All coordinates are in the projected CARLA coordinate system
    (output of Build 5 projection).
  - All randomization uses explicit seeds.
  - Every asset reference includes fallback metadata.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator, model_validator


# ── Coordinate helpers ─────────────────────────────────────────────────────

class WorldCoordinate(BaseModel):
    """Projected CARLA coordinate (x, y, z) in metres."""
    x: float
    y: float
    z: float = 0.0


class WorldBoundingBox(BaseModel):
    """Axis-aligned bounding box in projected CARLA space."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = 0.0
    max_z: float = 10.0

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.max_x <= self.min_x:
            raise ValueError("max_x must be > min_x")
        if self.max_y <= self.min_y:
            raise ValueError("max_y must be > min_y")
        if self.max_z <= self.min_z:
            raise ValueError("max_z must be > min_z")
        return self


# ── Asset reference with fallback metadata ────────────────────────────────

class AssetReference(BaseModel):
    """
    Reference to a simulator asset with explicit fallback chain.
    Never silently substitutes an asset.
    """
    semantic_class: str           # e.g. "palm_tree", "school_building"
    semantic_subtype: str = ""    # e.g. "tropical", "residential"
    resolved_asset_id: str        # e.g. "static.prop.palm_01"
    fallback_chain: List[str] = Field(default_factory=list)
    is_fallback: bool = False
    fallback_reason: Optional[str] = None

    def record_fallback(self, reason: str, fallback_asset_id: str):
        self.fallback_chain.append(fallback_asset_id)
        self.is_fallback = True
        self.fallback_reason = reason


# ── World object plans ────────────────────────────────────────────────────

class BuildingPlan(BaseModel):
    building_id: str
    semantic_type: str            # "residential", "commercial", "industrial", "education", "religious", "government"
    footprint: List[Tuple[float, float]]  # polygon corners in projected space
    height_m: float = Field(5.0, gt=0)
    rotation_deg: float = 0.0
    asset: Optional[AssetReference] = None
    geometry_fidelity: str = "approximate"  # "exact" | "approximate" | "fallback"
    source_osm_id: Optional[str] = None


class VegetationPlan(BaseModel):
    vegetation_id: str
    semantic_type: str            # "tree", "palm", "bush", "grass"
    position: WorldCoordinate
    height_m: float = Field(3.0, gt=0)
    rotation_deg: float = 0.0
    scale: float = Field(1.0, gt=0)
    asset: Optional[AssetReference] = None
    is_fallback: bool = False


class StreetFurniturePlan(BaseModel):
    furniture_id: str
    semantic_type: str            # "lamp_post", "barrier", "bollard", "bench", "parking_meter", "trash_bin", "guard_rail"
    position: WorldCoordinate
    rotation_deg: float = 0.0
    asset: Optional[AssetReference] = None
    is_fallback: bool = False


class SignPlan(BaseModel):
    sign_id: str
    sign_type: str                 # "stop", "speed_limit", "yield", "pedestrian_crossing", "traffic_light_ahead"
    value: Optional[float] = None  # e.g. 50 for speed_limit
    position: WorldCoordinate
    rotation_deg: float = 0.0
    asset: Optional[AssetReference] = None
    is_fallback: bool = False
    country: str = "usa"
    source: str = "country_profile"  # "country_profile" | "osm" | "scenario_override"


class TrafficLightPlan(BaseModel):
    traffic_light_id: str
    position: WorldCoordinate
    rotation_deg: float = 0.0
    asset: Optional[AssetReference] = None
    is_fallback: bool = False
    phase_duration_s: float = 30.0
    offset_s: float = 0.0
    country: str = "usa"
    source: str = "profile_default"


class VehiclePlan(BaseModel):
    vehicle_id: str
    semantic_type: str             # e.g. "sedan", "suv", "truck", "bus", "motorcycle", "bicycle", "auto_rickshaw"
    blueprint_id: Optional[str] = None
    position: WorldCoordinate
    rotation_deg: float = 0.0
    color: Optional[str] = None
    is_parked: bool = False
    is_ego: bool = False
    speed_ms: float = Field(0.0, ge=0.0, description="Speed in m/s (non-negative)")
    route: List[Tuple[float, float]] = Field(default_factory=list)


class PedestrianPlan(BaseModel):
    pedestrian_id: str
    position: WorldCoordinate
    rotation_deg: float = 0.0
    walking_speed_ms: float = 1.2
    destination: Optional[WorldCoordinate] = None
    group_id: Optional[str] = None
    crossing_probability: float = 0.1
    spawn_zone: str = "sidewalk"


class ScenarioEvent(BaseModel):
    event_id: str
    event_type: str                 # "lane_closure", "construction", "accident", "emergency_vehicle", "jaywalking", "puddle_zone"
    road_id: Optional[str] = None
    lane_id: Optional[str] = None
    position: Optional[WorldCoordinate] = None
    duration_s: float = 60.0
    severity: float = Field(0.5, ge=0.0, le=1.0)
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── Sensor configuration ──────────────────────────────────────────────────

class SensorConfig(BaseModel):
    sensor_id: str
    sensor_type: str                # "rgb", "lidar", "radar", "depth", "semantic", "instance", "optical_flow"
    position: WorldCoordinate
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # pitch, yaw, roll
    resolution: Optional[Tuple[int, int]] = None
    fov: Optional[float] = None
    sensor_tick: float = 0.1
    intrinsic: Optional[List[List[float]]] = None  # 3x3 K matrix
    extrinsic: Optional[List[List[float]]] = None  # 4x4 transform matrix
    noise_params: Dict[str, Any] = Field(default_factory=dict)

    @validator("resolution")
    def validate_resolution(cls, v):
        if v is not None:
            w, h = v
            if w <= 0 or h <= 0:
                raise ValueError(f"Resolution must be positive, got {v}")
        return v


# ── World Plan ────────────────────────────────────────────────────────────

class WorldPlan(BaseModel):
    """
    Deterministic plan for a procedurally generated simulation world.

    This is the central artifact of Build 6. It describes EVERYTHING
    that will be spawned in the simulator, before any simulator interaction.
    """
    world_id: str
    seed: int = Field(..., ge=0)
    location_query: str
    country: str
    map_name: str                    # e.g. "Town01" or "phase19_map"
    carla_coordinate_origin: WorldCoordinate

    # ── Object plans ──────────────────────────────────────────────────────────
    buildings: List[BuildingPlan] = Field(default_factory=list)
    vegetation: List[VegetationPlan] = Field(default_factory=list)
    street_furniture: List[StreetFurniturePlan] = Field(default_factory=list)
    signs: List[SignPlan] = Field(default_factory=list)
    traffic_lights: List[TrafficLightPlan] = Field(default_factory=list)
    vehicles: List[VehiclePlan] = Field(default_factory=list)
    pedestrians: List[PedestrianPlan] = Field(default_factory=list)
    events: List[ScenarioEvent] = Field(default_factory=list)

    # ── Sensors ───────────────────────────────────────────────────────────────
    sensors: List[SensorConfig] = Field(default_factory=list)

    # ── Environmental modifiers ───────────────────────────────────────────────
    weather_override: Optional[Dict[str, float]] = None
    time_of_day_override: Optional[str] = None

    # ── Bounds ────────────────────────────────────────────────────────────────
    bounding_box: Optional[WorldBoundingBox] = None

    # ── Provenance ────────────────────────────────────────────────────────────
    seeds: Dict[str, int] = Field(default_factory=dict)
    fallbacks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    asset_resolution_stats: Dict[str, int] = Field(default_factory=dict)  # {"exact": 84, "fallback": 16}

    def plan_hash(self) -> str:
        """Deterministic hash of the world plan for reproducibility checks."""
        payload = self.model_dump(exclude={"asset_resolution_stats", "fallbacks", "warnings"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Provenance ────────────────────────────────────────────────────────────

class WorldProvenance(BaseModel):
    """
    Extended provenance for Build 6 world generation.
    Build 5 provenance is preserved and extended.
    """
    # ── Input hashes ──────────────────────────────────────────────────────────
    country_profile_hash: str
    geography_hash: str
    world_plan_hash: str
    asset_registry_hash: str

    # ── Build metadata ────────────────────────────────────────────────────────
    build_version: str = "6.0.0"
    schema_version: str = "1.0.0"
    compiler_version: str = "1.0.0"
    git_commit: str = "unknown"

    # ── Seeds ────────────────────────────────────────────────────────────────
    world_seed: int = 0
    traffic_seed: int = 0
    pedestrian_seed: int = 0
    weather_seed: int = 0
    asset_seed: int = 0
    scenario_seed: int = 0

    # ── CARLA context ────────────────────────────────────────────────────────
    carla_version: str = "0.9.16"

    # ── Diagnostics ──────────────────────────────────────────────────────────
    fallbacks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    def provenance_hash(self) -> str:
        payload = self.model_dump(exclude={"git_commit"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
