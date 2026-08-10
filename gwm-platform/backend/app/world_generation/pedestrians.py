"""
app/world_generation/pedestrians.py — Build 6: Pedestrian population engine
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import PedestrianPlan, WorldCoordinate, WorldPlan


class PedestrianPopulationEngine:
    """Generates pedestrian population plans."""

    def __init__(self, world_plan: WorldPlan, country_profile: Dict[str, Any], resolved_scenario: Dict[str, Any]):
        self.world_plan = world_plan
        self.country_profile = country_profile
        self.resolved = resolved_scenario
        self.seed = world_plan.seed

    def generate(self, density: float = 0.3, time_of_day: str = "noon", weather: str = "sunny") -> List[PedestrianPlan]:
        rng = random.Random(self.seed + 5000)
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        # Density modifiers
        time_mod = {"morning": 0.8, "noon": 0.5, "sunset": 0.9, "evening": 0.8, "night": 0.2, "golden hour": 0.7}
        weather_mod = {"rain": 0.4, "heavy_rain": 0.2, "fog": 0.5, "dust_storm": 0.3}
        t_mod = time_mod.get(time_of_day, 0.5)
        w_mod = weather_mod.get(weather, 1.0)

        count = int(40 * density * t_mod * w_mod)
        plans = []

        for i in range(count):
            x = rng.uniform(bbox.min_x + 0.5, bbox.max_x - 0.5)
            y = rng.uniform(bbox.min_y + 0.5, bbox.max_y - 0.5)

            plan = PedestrianPlan(
                pedestrian_id=f"ped_{i:04d}",
                position=WorldCoordinate(x=x, y=y, z=0.0),
                rotation_deg=rng.uniform(0, 360),
                walking_speed_ms=rng.uniform(0.8, 1.8),
                destination=WorldCoordinate(
                    x=rng.uniform(bbox.min_x, bbox.max_x),
                    y=rng.uniform(bbox.min_y, bbox.max_y),
                    z=0.0,
                ),
                crossing_probability=0.1,
                spawn_zone="sidewalk",
            )
            plans.append(plan)

        return plans
