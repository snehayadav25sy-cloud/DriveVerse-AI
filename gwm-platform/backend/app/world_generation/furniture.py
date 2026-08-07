"""
app/world_generation/furniture.py — Build 6: Street furniture engine

Generates deterministic street furniture placements.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import StreetFurniturePlan, WorldCoordinate, WorldPlan


class StreetFurnitureEngine:
    """Generates street furniture placement plans."""

    def __init__(self, world_plan: WorldPlan):
        self.world_plan = world_plan
        self.seed = world_plan.seed

    def generate(
        self,
        density: float = 0.3,
        road_types: List[str] = None,
    ) -> List[StreetFurniturePlan]:
        rng = random.Random(self.seed + 1000)
        road_types = road_types or ["urban", "residential"]
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        furniture_types = [
            "lamp_post", "lamp_post", "barrier", "bollard",
            "bench", "parking_meter", "trash_bin", "guard_rail"
        ]
        count = int(30 * density)
        plans = []

        for i in range(count):
            x = rng.uniform(bbox.min_x + 1.0, bbox.max_x - 1.0)
            y = rng.uniform(bbox.min_y + 1.0, bbox.max_y - 1.0)
            ftype = rng.choice(furniture_types)
            plan = StreetFurniturePlan(
                furniture_id=f"furn_{i:04d}",
                semantic_type=ftype,
                position=WorldCoordinate(x=x, y=y, z=0.0),
                rotation_deg=rng.uniform(0, 360),
            )
            plans.append(plan)

        return plans
