"""
app/world_generation/vehicles.py — Build 6: Vehicle population engine

Generates vehicle population plans based on:
  - CountryProfile vehicle mix
  - traffic density
  - road type
  - time of day
  - scenario modifiers
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import VehiclePlan, WorldCoordinate, WorldPlan


class VehiclePopulationEngine:
    """Generates vehicle population plans."""

    def __init__(self, world_plan: WorldPlan, country_profile: Dict[str, Any], resolved_scenario: Dict[str, Any]):
        self.world_plan = world_plan
        self.country_profile = country_profile
        self.resolved = resolved_scenario
        self.seed = world_plan.seed

    def generate(self, traffic_density: str = "normal") -> List[VehiclePlan]:
        rng = random.Random(self.seed + 4000)
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        vehicle_mix = self.country_profile.get("vehicle_mix", {"sedan": 0.5, "suv": 0.3, "truck": 0.2})
        density_map = {"low": 10, "normal": 30, "heavy": 60}
        count = density_map.get(traffic_density, 30)

        plans = []
        types = list(vehicle_mix.keys())
        weights = list(vehicle_mix.values())

        for i in range(count):
            vtype = rng.choices(types, weights=weights, k=1)[0]
            x = rng.uniform(bbox.min_x + 1.0, bbox.max_x - 1.0)
            y = rng.uniform(bbox.min_y + 1.0, bbox.max_y - 1.0)

            plan = VehiclePlan(
                vehicle_id=f"veh_{i:04d}",
                semantic_type=vtype,
                position=WorldCoordinate(x=x, y=y, z=0.0),
                rotation_deg=rng.uniform(0, 360),
                is_ego=(i == 0),
                speed_ms=rng.uniform(0, 15.0),
            )
            plans.append(plan)

        return plans
