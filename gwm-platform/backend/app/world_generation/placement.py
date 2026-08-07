"""
app/world_generation/placement.py — Build 6: Building placement engine

Converts OSM building data and semantic types into BuildingPlan objects
with deterministic placement, collision awareness, and spacing rules.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import (
    BuildingPlan,
    WorldBoundingBox,
    WorldCoordinate,
    WorldPlan,
)


# OSM building tag -> semantic type mapping
OSM_BUILDING_SEMANTIC_MAP = {
    "residential": "residential",
    "house": "residential",
    "apartments": "residential",
    "commercial": "commercial",
    "office": "commercial",
    "retail": "retail",
    "shop": "retail",
    "industrial": "industrial",
    "warehouse": "industrial",
    "school": "education",
    "university": "education",
    "college": "education",
    "hospital": "hospital",
    "church": "religious",
    "mosque": "religious",
    "temple": "religious",
    "government": "government",
    "townhall": "government",
    "hotel": "commercial",
}


class BuildingPlacementEngine:
    """
    Places buildings in the world plan based on geographic data.
    """

    def __init__(
        self,
        world_plan: WorldPlan,
        min_spacing_m: float = 2.0,
        road_buffer_m: float = 1.0,
    ):
        self.world_plan = world_plan
        self.min_spacing_m = min_spacing_m
        self.road_buffer_m = road_buffer_m
        self._placed_buildings: List[BuildingPlan] = []

    def place_from_osm_buildings(self, osm_buildings: List[Dict[str, Any]]) -> List[BuildingPlan]:
        """
        Place buildings from OSM building metadata.
        Each OSM building dict should contain:
          - osm_id
          - building type tag
          - geometry (list of lon/lat or projected x/y)
          - name (optional)
        """
        plans = []
        for b in osm_buildings:
            semantic_type = self._osm_to_semantic(b.get("building", "generic"))
            geometry = b.get("geometry", [])
            if not geometry:
                continue

            # Convert geometry to projected coordinates if needed
            footprint = self._convert_footprint(geometry)
            centroid = self._compute_centroid(footprint)
            height_m = self._estimate_height(semantic_type, b)

            # Check spacing
            if self._violates_spacing(centroid):
                continue

            plan = BuildingPlan(
                building_id=b.get("osm_id", f"b_{len(plans)}"),
                semantic_type=semantic_type,
                footprint=footprint,
                height_m=height_m,
                rotation_deg=0.0,
                geometry_fidelity="exact" if len(footprint) >= 3 else "approximate",
                source_osm_id=b.get("osm_id"),
            )
            plans.append(plan)
            self._placed_buildings.append(plan)

        return plans

    def _osm_to_semantic(self, osm_tag: str) -> str:
        tag = (osm_tag or "generic").lower().strip()
        return OSM_BUILDING_SEMANTIC_MAP.get(tag, "generic")

    def _convert_footprint(self, geometry: Any) -> List[Tuple[float, float]]:
        if isinstance(geometry, list) and len(geometry) > 0:
            if isinstance(geometry[0], dict):
                return [(p.get("x", 0.0), p.get("y", 0.0)) for p in geometry]
            if isinstance(geometry[0], (tuple, list)) and len(geometry[0]) >= 2:
                return [(float(p[0]), float(p[1])) for p in geometry]
        return [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]

    def _compute_centroid(self, footprint: List[Tuple[float, float]]) -> Tuple[float, float]:
        if not footprint:
            return (0.0, 0.0)
        xs = [p[0] for p in footprint]
        ys = [p[1] for p in footprint]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _estimate_height(self, semantic_type: str, building: Dict[str, Any]) -> float:
        heights = {
            "residential": 12.0,
            "commercial": 30.0,
            "retail": 10.0,
            "industrial": 15.0,
            "education": 15.0,
            "hospital": 25.0,
            "religious": 20.0,
            "government": 25.0,
            "generic": 10.0,
        }
        base = heights.get(semantic_type, 10.0)
        levels = building.get("building:levels")
        if levels and str(levels).isdigit():
            return float(levels) * 3.0
        return base

    def _violates_spacing(self, centroid: Tuple[float, float]) -> bool:
        for placed in self._placed_buildings:
            pc = self._compute_centroid(placed.footprint)
            dist = math.hypot(centroid[0] - pc[0], centroid[1] - pc[1])
            if dist < self.min_spacing_m:
                return True
        return False
