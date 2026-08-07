"""
app/world_generation/events.py — Build 6: Scenario event engine
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from app.world_generation.models import ScenarioEvent, WorldPlan


class ScenarioEventEngine:
    """Generates semantic scenario event plans."""

    EVENT_TYPES = [
        "lane_closure",
        "construction",
        "parked_vehicle",
        "broken_down_vehicle",
        "pedestrian_crossing",
        "jaywalking",
        "accident",
        "emergency_vehicle",
        "sudden_braking",
        "lane_blockage",
        "puddle_zone",
    ]

    def __init__(self, world_plan: WorldPlan):
        self.world_plan = world_plan
        self.seed = world_plan.seed

    def generate(self, event_count: int = 3) -> List[ScenarioEvent]:
        rng = random.Random(self.seed + 6000)
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return []

        plans = []
        for i in range(min(event_count, len(self.EVENT_TYPES))):
            etype = self.EVENT_TYPES[i % len(self.EVENT_TYPES)]
            x = rng.uniform(bbox.min_x, bbox.max_x)
            y = rng.uniform(bbox.min_y, bbox.max_y)

            plan = ScenarioEvent(
                event_id=f"event_{i:04d}",
                event_type=etype,
                position=None,  # Will be set for position-based events
                duration_s=rng.uniform(30, 300),
                severity=rng.uniform(0.3, 1.0),
                active=True,
                metadata={"generated_by": "ScenarioEventEngine", "seed": self.seed},
            )
            if etype in ["lane_closure", "lane_blockage", "construction", "puddle_zone"]:
                plan.position = None  # Road-based events
            else:
                plan.position = {"x": x, "y": y}

            plans.append(plan)

        return plans
