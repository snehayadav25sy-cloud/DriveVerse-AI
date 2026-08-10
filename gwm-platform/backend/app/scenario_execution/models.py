"""
app/scenario_execution/models.py — Build 7: Execution session schema (Pydantic v2)

Design:
  - No CARLA imports here.
  - Simulator-independent execution model.
  - Deterministic seeds for reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────

class SessionStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    DEPLOYING_MAP = "DEPLOYING_MAP"
    READY = "READY"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MapProviderType(str, Enum):
    TOWN = "town"
    OPENDRIVE_ARTIFACT = "opendrive_artifact"


class MapDeploymentStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEPLOYMENT_REQUIRED = "DEPLOYMENT_REQUIRED"
    DEPLOYING = "DEPLOYING"
    DEPLOYED = "DEPLOYED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


class ActorStatus(str, Enum):
    SPAWNED = "SPAWNED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DESTROYED = "DESTROYED"
    FAILED = "FAILED"


class EventType(str, Enum):
    TRAFFIC_LIGHT_CHANGE = "TRAFFIC_LIGHT_CHANGE"
    PEDESTRIAN_CROSSING = "PEDESTRIAN_CROSSING"
    JAYWALKING = "JAYWALKING"
    VEHICLE_BRAKING = "VEHICLE_BRAKING"
    VEHICLE_CUT_IN = "VEHICLE_CUT_IN"
    LANE_CHANGE = "LANE_CHANGE"
    LANE_CLOSURE = "LANE_CLOSURE"
    ACCIDENT = "ACCIDENT"
    ROAD_CONSTRUCTION = "ROAD_CONSTRUCTION"
    EMERGENCY_VEHICLE = "EMERGENCY_VEHICLE"
    DEBRIS = "DEBRIS"
    PUDDLE_ZONE = "PUDDLE_ZONE"
    SUDDEN_OBSTACLE = "SUDDEN_OBSTACLE"
    WEATHER_CHANGE = "WEATHER_CHANGE"


class TriggerType(str, Enum):
    TIME_TRIGGER = "TIME_TRIGGER"
    DISTANCE_TRIGGER = "DISTANCE_TRIGGER"
    PROXIMITY_TRIGGER = "PROXIMITY_TRIGGER"
    ACTOR_STATE_TRIGGER = "ACTOR_STATE_TRIGGER"
    TRAFFIC_TRIGGER = "TRAFFIC_TRIGGER"
    WEATHER_TRIGGER = "WEATHER_TRIGGER"
    RANDOM_TRIGGER = "RANDOM_TRIGGER"


class ActorType(str, Enum):
    VEHICLE = "vehicle"
    PEDESTRIAN = "pedestrian"
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    EMERGENCY_VEHICLE = "emergency_vehicle"
    STATIC_ACTOR = "static_actor"


class SimulatorType(str, Enum):
    CARLA = "carla"


# ── Coordinate ─────────────────────────────────────────────────────────────

class ExecutionCoordinate(BaseModel):
    """Simulator coordinate."""
    x: float
    y: float
    z: float = 0.0


# ── Actor models ──────────────────────────────────────────────────────────

class ActorState(BaseModel):
    actor_id: str
    actor_type: ActorType
    semantic_class: str
    blueprint_id: Optional[str] = None
    role: str = "traffic"
    position: ExecutionCoordinate
    rotation_deg: float = 0.0
    speed_ms: float = 0.0
    behavior_profile: Dict[str, Any] = Field(default_factory=dict)
    seed: int = 0
    status: ActorStatus = ActorStatus.SPAWNED


class VehicleActorState(ActorState):
    actor_type: ActorType = ActorType.VEHICLE
    is_ego: bool = False
    is_parked: bool = False
    target_speed_ms: float = 10.0
    lane_id: Optional[str] = None
    route: List[Tuple[float, float]] = Field(default_factory=list)


class PedestrianActorState(ActorState):
    actor_type: ActorType = ActorType.PEDESTRIAN
    walking_speed_ms: float = 1.2
    destination: Optional[ExecutionCoordinate] = None
    crossing_probability: float = 0.1
    spawn_zone: str = "sidewalk"


# ── Event models ──────────────────────────────────────────────────────────

class EventTrigger(BaseModel):
    trigger_type: TriggerType
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScenarioEventPlan(BaseModel):
    event_id: str
    event_type: EventType
    trigger: EventTrigger
    start_time_s: float = 0.0
    duration_s: float = 10.0
    priority: int = 0
    affected_actor_ids: List[str] = Field(default_factory=list)
    action: Dict[str, Any] = Field(default_factory=dict)
    seed: int = 0
    executed: bool = False
    execution_time_s: Optional[float] = None


# ── Sensor models ──────────────────────────────────────────────────────────

class SensorState(BaseModel):
    sensor_id: str
    sensor_type: str
    position: ExecutionCoordinate
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    resolution: Optional[Tuple[int, int]] = None
    fov: Optional[float] = None
    frequency_hz: float = 10.0
    calibration: Dict[str, Any] = Field(default_factory=dict)
    healthy: bool = True
    frame_count: int = 0


# ── Map models ─────────────────────────────────────────────────────────────

class MapConfig(BaseModel):
    provider: MapProviderType = MapProviderType.TOWN
    map_name: str = "Town01"
    deployment_required: bool = False
    deployment_instructions: List[str] = Field(default_factory=list)
    artifact_path: Optional[str] = None


# ── Timing models ──────────────────────────────────────────────────────────

class TimingConfig(BaseModel):
    fixed_delta_seconds: float = Field(0.05, gt=0.0)
    total_simulation_seconds: float = Field(30.0, gt=0.0)
    max_wall_seconds: Optional[float] = None


# ── Execution session ──────────────────────────────────────────────────────

class ExecutionSession(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    world_plan_id: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATED

    simulator: Dict[str, str] = Field(default_factory=lambda: {"name": "carla", "version": "0.9.16"})
    map: MapConfig = Field(default_factory=MapConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)

    seeds: Dict[str, int] = Field(default_factory=dict)

    actors: List[ActorState] = Field(default_factory=list)
    sensors: List[SensorState] = Field(default_factory=list)
    events: List[ScenarioEventPlan] = Field(default_factory=list)

    recording: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    current_frame: int = 0
    current_simulation_time_s: float = 0.0

    @model_validator(mode="after")
    def validate_seeds(self):
        required_seeds = ["master_seed", "traffic_seed", "spawn_seed", "event_seed", "weather_seed", "sensor_seed"]
        for s in required_seeds:
            if s not in self.seeds:
                self.seeds[s] = 0
        return self


# ── Preflight ──────────────────────────────────────────────────────────────

class PreflightCheck(BaseModel):
    name: str
    passed: bool
    message: Optional[str] = None


class ExecutionPreflightReport(BaseModel):
    passed: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks: List[PreflightCheck] = Field(default_factory=list)


# ── Validation ─────────────────────────────────────────────────────────────

class DatasetValidationReport(BaseModel):
    passed: bool
    expected_frames: int = 0
    actual_frames: int = 0
    missing_frames: List[int] = Field(default_factory=list)
    corrupt_files: List[str] = Field(default_factory=list)
    sensor_sync: bool = False
    metadata_complete: bool = False
    provenance_complete: bool = False
    details: List[str] = Field(default_factory=list)


class SynchronizationReport(BaseModel):
    synchronized: bool
    total_frames: int
    missing_sensor_frames: Dict[str, List[int]] = Field(default_factory=dict)
    duplicate_frames: List[int] = Field(default_factory=list)
    out_of_order_frames: List[int] = Field(default_factory=list)
    timestamp_drift_s: float = 0.0


# ── Recording ──────────────────────────────────────────────────────────────

class RecordingManifest(BaseModel):
    session_id: str
    frame_count: int
    sensors: List[str] = Field(default_factory=list)
    start_frame: int = 0
    end_frame: int = 0
    complete: bool = False
    output_directory: str = ""


class FrameIndexEntry(BaseModel):
    frame_id: int
    rgb: Optional[str] = None
    lidar: Optional[str] = None
    radar: Optional[str] = None
    depth: Optional[str] = None
    semantic: Optional[str] = None
    instance: Optional[str] = None
    optical_flow: Optional[str] = None
    annotations: Optional[str] = None


class Checkpoint(BaseModel):
    checkpoint_id: str
    session_id: str
    simulation_frame: int = 0
    simulation_time_s: float = 0.0
    actor_states: List[Dict[str, Any]] = Field(default_factory=list)
    event_state: Dict[str, Any] = Field(default_factory=dict)
    random_state: Dict[str, Any] = Field(default_factory=dict)
    sensor_state: Dict[str, Any] = Field(default_factory=dict)
    output_state: Dict[str, Any] = Field(default_factory=dict)


# ── Execution provenance ──────────────────────────────────────────────────

class ExecutionProvenance(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    world_plan_id: Optional[str] = None
    country_profile_version: str = "1.0.0"
    geography_hash: str = ""
    world_plan_hash: str = ""
    scenario_hash: str = ""
    simulator_name: str = "carla"
    simulator_version: str = "0.9.16"
    git_commit: str = "unknown"
    build_version: str = "7.0.0"
    master_seed: int = 0
    traffic_seed: int = 0
    spawn_seed: int = 0
    event_seed: int = 0
    weather_seed: int = 0
    sensor_seed: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    logical_replayable: bool = True
    physical_replayable: bool = False

    def provenance_hash(self) -> str:
        payload = self.model_dump(exclude={"git_commit", "start_time", "end_time"})
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Errors ─────────────────────────────────────────────────────────────────

class ExecutionError(BaseModel):
    code: str
    message: str
    phase: str
    recoverable: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)
