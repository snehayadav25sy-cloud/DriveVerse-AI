"""
app/world_generation/vegetation.py — Build 6: Vegetation placement engine

Generates deterministic vegetation placements based on:
  - country
  - climate
  - road type
  - season
  - weather
  - random seed
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from app.world_generation.models import VegetationPlan, WorldCoordinate, WorldPlan


# Country -> default vegetation profiles
COUNTRY_VEGETATION_PROFILES: Dict[str, Dict[str, Any]] = {
    "india": {
        "default": {"tree": 0.4, "palm": 0.3, "bush": 0.2, "grass": 0.1},
        "tropical": {"tree": 0.3, "palm": 0.5, "bush": 0.15, "grass": 0.05},
        "monsoon": {"tree": 0.5, "palm": 0.2, "bush": 0.2, "grass": 0.1},
    },
    "dubai": {
        "default": {"tree": 0.1, "palm": 0.6, "bush": 0.2, "grass": 0.1},
        "desert": {"tree": 0.05, "palm": 0.5, "bush": 0.3, "grass": 0.15},
    },
    "germany": {
        "default": {"tree": 0.6, "palm": 0.0, "bush": 0.25, "grass": 0.15},
        "temperate": {"tree": 0.65, "palm": 0.0, "bush": 0.2, "grass": 0.15},
    },
    "japan": {
        "default": {"tree": 0.5, "palm": 0.0, "bush": 0.3, "grass": 0.2},
        "urban": {"tree": 0.3, "palm": 0.0, "bush": 0.4, "grass": 0.3},
    },
    "usa": {
        "default": {"tree": 0.5, "palm": 0.1, "bush": 0.25, "grass": 0.15},
        "suburban": {"tree": 0.6, "palm": 0.0, "bush": 0.2, "grass": 0.2},
    },
    "uk": {
        "default": {"tree": 0.55, "palm": 0.0, "bush": 0.3, "grass": 0.15},
        "temperate": {"tree": 0.6, "palm": 0.0, "bush": 0.25, "grass": 0.15},
    },
}

SEASON_MODIFIERS = {
    "spring": {"density": 1.0, "height_variation": 0.1},
    "summer": {"density": 1.2, "height_variation": 0.15},
    "autumn": {"density": 0.9, "height_variation": 0.2},
    "winter": {"density": 0.6, "height_variation": 0.05},
}


class VegetationEngine:
    """Generates vegetation placement plans."""

    def __init__(self, world_plan: WorldPlan):
        self.world_plan = world_plan
        self.country = world_plan.country.lower()
        self.seed = world_plan.seed

    def generate(
        self,
        density: float = 0.5,
        season: str = "summer",
        climate: str = "default",
    ) -> List[VegetationPlan]:
        """
        Generate vegetation plans.
        """
        rng = random.Random(self.seed)
        profile = COUNTRY_VEGETATION_PROFILES.get(self.country, COUNTRY_VEGETATION_PROFILES["usa"])
        climate_profile = profile.get(climate, profile.get("default", {"tree": 0.5, "palm": 0.1, "bush": 0.25, "grass": 0.15}))
        season_mod = SEASON_MODIFIERS.get(season, SEASON_MODIFIERS["summer"])

        plans = []
        count = int(50 * density * season_mod["density"])
        bbox = self.world_plan.bounding_box
        if bbox is None:
            return plans

        for i in range(count):
            x = rng.uniform(bbox.min_x + 2.0, bbox.max_x - 2.0)
            y = rng.uniform(bbox.min_y + 2.0, bbox.max_y - 2.0)
            z = 0.0

            # Select vegetation type based on profile weights
            veg_type = self._weighted_choice(rng, climate_profile)
            height = self._height_for_type(veg_type, rng, season_mod["height_variation"])

            plan = VegetationPlan(
                vegetation_id=f"veg_{i:04d}",
                semantic_type=veg_type,
                position=WorldCoordinate(x=x, y=y, z=z),
                height_m=height,
                rotation_deg=rng.uniform(0, 360),
                scale=rng.uniform(0.8, 1.2),
            )
            plans.append(plan)

        return plans

    def _weighted_choice(self, rng: random.Random, weights: Dict[str, float]) -> str:
        items = list(weights.keys())
        total = sum(weights.values())
        if total == 0:
            return "tree"
        r = rng.random() * total
        cumsum = 0.0
        for item in items:
            cumsum += weights[item]
            if r <= cumsum:
                return item
        return items[-1]

    def _height_for_type(self, veg_type: str, rng: random.Random, variation: float) -> float:
        bases = {"tree": 8.0, "palm": 10.0, "bush": 1.5, "grass": 0.3}
        base = bases.get(veg_type, 3.0)
        return max(0.1, base + rng.uniform(-variation, variation) * base)
