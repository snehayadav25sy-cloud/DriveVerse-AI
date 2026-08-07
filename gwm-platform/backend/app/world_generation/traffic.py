"""
app/world_generation/traffic.py — Build 6: Traffic sign and light engines
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import SignPlan, TrafficLightPlan, WorldCoordinate, WorldPlan


class TrafficSignEngine:
    """Generates traffic sign placement plans based on country rules."""

    def __init__(self, world_plan: WorldPlan, country_profile: Dict[str, Any]):
        self.world_plan = world_plan
        self.country_profile = country_profile
        self.seed = world_plan.seed

    def generate(self, density: float = 0.2) -> List[SignPlan]:
        rng = random.Random(self.seed + 2000)
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        sign_types = ["stop", "speed_limit", "yield", "pedestrian_crossing"]
        count = int(20 * density)
        plans = []

        for i in range(count):
            x = rng.uniform(bbox.min_x + 1.0, bbox.max_x - 1.0)
            y = rng.uniform(bbox.min_y + 1.0, bbox.max_y - 1.0)
            stype = rng.choice(sign_types)
            value = 50.0 if stype == "speed_limit" else None

            plan = SignPlan(
                sign_id=f"sign_{i:04d}",
                sign_type=stype,
                value=value,
                position=WorldCoordinate(x=x, y=y, z=0.0),
                rotation_deg=rng.uniform(0, 360),
                country=self.world_plan.country,
                source="country_profile",
            )
            plans.append(plan)

        return plans


class TrafficLightEngine:
    """Generates traffic light plans for intersections."""

    def __init__(self, world_plan: WorldPlan, country_profile: Dict[str, Any]):
        self.world_plan = world_plan
        self.country_profile = country_profile
        self.seed = world_plan.seed

    def generate(self, intersection_count: int = 5) -> List[TrafficLightPlan]:
        rng = random.Random(self.seed + 3000)
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        plans = []
        count = min(intersection_count, 20)
        for i in range(count):
            x = rng.uniform(bbox.min_x + 2.0, bbox.max_x - 2.0)
            y = rng.uniform(bbox.min_y + 2.0, bbox.max_y - 2.0)

            plan = TrafficLightPlan(
                traffic_light_id=f"tl_{i:04d}",
                position=WorldCoordinate(x=x, y=y, z=0.0),
                rotation_deg=rng.uniform(0, 360),
                phase_duration_s=30.0,
                offset_s=rng.uniform(0, 30),
                country=self.world_plan.country,
                source="profile_default",
            )
            plans.append(plan)

        return plans
