"""
app/geography/models.py — Build 5: Geographic schema (Pydantic v2)

This module defines the core geographic data models for the Geography Engine.
It reuses/extends the existing ScenarioConfig from the backend schema rather
than duplicating it.

Models:
  GeoCoordinate     — WGS84 latitude/longitude/altitude
  BoundingBox       — geographic bounding box (south/north/west/east)
  LocationRequest   — user request for a geographic location
  LocationResolution — resolved geocoder result
  Road              — OSM way metadata
  Lane              — lane within a road
  Intersection      — node where roads meet
  TrafficSignal     — traffic light/sign metadata
  Crosswalk         — pedestrian crossing metadata
  RoadNode          — node in the road graph
  RoadEdge          — edge in the road graph
  RoadGraph         — full road network graph
  GeographicScenario — ScenarioConfig + geographic fields
  MapArtifact       — compiled OpenDRIVE artifact
  MapProvenance     — full pipeline provenance
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator, model_validator

# Ensure backend app package is importable from app/geography
_backend_root = Path(__file__).parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.schemas.scenario import ScenarioConfig


# ── Coordinate / BoundingBox ─────────────────────────────────────────────

class GeoCoordinate(BaseModel):
    """WGS84 geographic coordinate."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Decimal degrees")
    altitude: float = Field(0.0, description="Metres above sea level")


class BoundingBox(BaseModel):
    """Geographic bounding box in WGS84."""
    south: float = Field(..., ge=-90.0, le=90.0)
    north: float = Field(..., ge=-90.0, le=90.0)
    west: float = Field(..., ge=-180.0, le=180.0)
    east: float = Field(..., ge=-180.0, le=180.0)

    @validator("north")
    def north_gt_south(cls, v, values):
        south = values.get("south")
        if south is not None and v <= south:
            raise ValueError(f"north ({v}) must be > south ({south})")
        return v

    @validator("east")
    def east_gt_west(cls, v, values):
        west = values.get("west")
        if west is not None and v <= west:
            raise ValueError(f"east ({v}) must be > west ({west})")
        return v


# ── Geocoder results ────────────────────────────────────────────────────

class LocationRequest(BaseModel):
    """User-supplied location request."""
    location: Optional[str] = Field(None, min_length=1, description="Free-text location query")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Explicit latitude (bypass geocoding)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Explicit longitude (bypass geocoding)")
    radius_m: float = Field(500.0, gt=0, description="Radius in metres for OSM download")
    country: Optional[str] = Field(None, description="Optional country override")
    provider: str = Field("nominatim", description="Geocoder provider name")

    @validator("location")
    def location_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("location must not be empty")
        return v.strip() if v else v

    @validator("latitude", "longitude")
    def coords_mutually_exclusive_with_location(cls, v, values):
        # Allow explicit coords without location, but if location is given,
        # coords are optional and not validated against each other here.
        return v

    @model_validator(mode="after")
    def at_least_one_location_source(self):
        if not self.location and (self.latitude is None or self.longitude is None):
            raise ValueError(
                "At least one of 'location' or both 'latitude' and 'longitude' must be provided"
            )
        return self


class LocationResolution(BaseModel):
    """Resolved geocoder result."""
    query: str
    provider: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    raw: Optional[Dict[str, Any]] = None
    cached: bool = False
    timestamp: Optional[str] = None


# ── OSM / Road primitives ───────────────────────────────────────────────

class Lane(BaseModel):
    """Single lane within a road."""
    id: str
    width: float = Field(3.5, gt=0)
    direction: str = Field("forward", pattern="^(forward|backward|both)$")
    is_driving: bool = True
    is_shoulder: bool = False
    is_parking: bool = False


class Road(BaseModel):
    """OSM way metadata."""
    osm_id: str
    name: Optional[str] = None
    highway_type: str
    lanes: int = Field(1, ge=1)
    maxspeed: Optional[float] = None
    oneway: bool = False
    surface: Optional[str] = None
    bridge: bool = False
    tunnel: bool = False
    country: Optional[str] = None
    source_osm_id: Optional[str] = None
    geometry: List[Tuple[float, float]] = Field(default_factory=list, description="List of (lon, lat) pairs")


class Intersection(BaseModel):
    """Node where roads meet."""
    node_id: str
    latitude: float
    longitude: float
    incoming_roads: List[str] = Field(default_factory=list)
    outgoing_roads: List[str] = Field(default_factory=list)
    traffic_signal: bool = False


class TrafficSignal(BaseModel):
    """Traffic light or sign."""
    osm_id: str
    latitude: float
    longitude: float
    signal_type: str = Field("traffic_light", description="traffic_light | stop | give_way")
    lanes: List[str] = Field(default_factory=list)


class Crosswalk(BaseModel):
    """Pedestrian crossing."""
    osm_id: str
    latitude: float
    longitude: float
    crossing_type: str = Field("marked", description="marked | unmarked | traffic_signals")
    lanes: List[str] = Field(default_factory=list)


# ── Road graph ──────────────────────────────────────────────────────────

class RoadNode(BaseModel):
    """Node in the road graph (intersection or endpoint)."""
    node_id: str
    coordinate: GeoCoordinate
    node_type: str = Field("intersection", description="intersection | endpoint | dead_end | merge | split")
    roads: List[str] = Field(default_factory=list)


class RoadEdge(BaseModel):
    """Edge in the road graph (road segment)."""
    edge_id: str
    from_node: str
    to_node: str
    road: Road
    length_m: float = Field(..., gt=0)
    lane_count: int = Field(1, ge=1)


class RoadGraph(BaseModel):
    """Full road network graph."""
    nodes: List[RoadNode] = Field(default_factory=list)
    edges: List[RoadEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return len(self.edges)

    def intersection_count(self) -> int:
        return sum(1 for n in self.nodes if n.node_type == "intersection")


# ── Scenario / Artifact / Provenance ────────────────────────────────────

class GeographicScenario(ScenarioConfig):
    """
    ScenarioConfig extended with geographic location fields.
    Inherits all Build 3/4 fields (sensors, frames, weather, traffic, etc.)
    and adds Build 5 geographic resolution data.
    """
    # ── Geographic resolution ──────────────────────────────────────────────
    location_query: Optional[str] = Field(None, description="Original user location query")
    origin_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    origin_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    bbox: Optional[BoundingBox] = None
    resolution: Optional[LocationResolution] = None
    road_graph: Optional[RoadGraph] = None
    map_artifact: Optional[MapArtifact] = None


class MapArtifact(BaseModel):
    """Compiled OpenDRIVE map artifact."""
    xodr_path: Optional[str] = None
    xodr_size_bytes: int = 0
    xodr_hash: Optional[str] = None
    validator_passed: bool = False
    validator_errors: List[str] = Field(default_factory=list)
    validator_warnings: List[str] = Field(default_factory=list)
    carla_map_name: Optional[str] = None
    carla_load_succeeded: Optional[bool] = None
    carla_spawn_point_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MapProvenance(BaseModel):
    """Full pipeline provenance for a geographic map build."""
    # ── Input ──────────────────────────────────────────────────────────────
    location_query: str
    radius_m: float
    geocoder_provider: str
    osm_provider: str

    # ── Geocoder ───────────────────────────────────────────────────────────
    resolved_latitude: Optional[float] = None
    resolved_longitude: Optional[float] = None
    resolved_country: Optional[str] = None
    resolved_city: Optional[str] = None
    bbox: Optional[Dict[str, float]] = None

    # ── OSM ───────────────────────────────────────────────────────────────
    osm_file_path: Optional[str] = None
    osm_file_size_bytes: int = 0
    osm_timestamp: Optional[str] = None
    osm_source_hash: Optional[str] = None

    # ── Graph ─────────────────────────────────────────────────────────────
    road_graph_node_count: int = 0
    road_graph_edge_count: int = 0
    road_graph_hash: Optional[str] = None

    # ── OpenDRIVE ─────────────────────────────────────────────────────────
    xodr_hash: Optional[str] = None
    compiler_version: str = "1.0.0"
    schema_version: str = "1.0.0"

    # ── Build 4 context ───────────────────────────────────────────────────
    country_profile_version: Optional[str] = None
    carla_version: str = "0.9.16"

    # ── VCS / Seeds ───────────────────────────────────────────────────────
    git_commit: str = "unknown"
    random_seed: Optional[int] = None

    # ── Diagnostics ───────────────────────────────────────────────────────
    fallbacks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
