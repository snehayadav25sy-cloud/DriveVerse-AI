"""
app/world_generation/randomization.py — Build 6: Domain randomization engine

Implements deterministic randomization using explicit seeds.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional


class DomainRandomizer:
    """
    Deterministic domain randomizer.

    Every randomization dimension uses an explicit seed.
    Never uses uncontrolled random.random().
    """

    def __init__(self, seeds: Dict[str, int]):
        self.seeds = seeds
        self._rngs: Dict[str, random.Random] = {}
        for name, seed in seeds.items():
            self._rngs[name] = random.Random(seed)

    def get_rng(self, domain: str) -> random.Random:
        if domain not in self._rngs:
            self._rngs[domain] = random.Random(self.seeds.get(domain, 0))
        return self._rngs[domain]

    def randomize_weather(self, base_weather: Dict[str, float]) -> Dict[str, float]:
        rng = self.get_rng("weather")
        return {
            "cloudiness": max(0.0, min(100.0, base_weather.get("cloudiness", 0.0) + rng.uniform(-10, 10))),
            "precipitation": max(0.0, min(100.0, base_weather.get("precipitation", 0.0) + rng.uniform(-5, 5))),
            "wind_intensity": max(0.0, min(100.0, base_weather.get("wind_intensity", 0.0) + rng.uniform(-5, 5))),
            "fog_density": max(0.0, min(100.0, base_weather.get("fog_density", 0.0) + rng.uniform(-3, 3))),
        }

    def randomize_vehicle_color(self, semantic_type: str) -> str:
        rng = self.get_rng("asset")
        colors = ["red", "blue", "white", "black", "silver", "gray", "green", "yellow"]
        return rng.choice(colors)

    def randomize_spawn_jitter(self, base_position: Dict[str, float], jitter_m: float = 0.5) -> Dict[str, float]:
        rng = self.get_rng("world")
        return {
            "x": base_position.get("x", 0.0) + rng.uniform(-jitter_m, jitter_m),
            "y": base_position.get("y", 0.0) + rng.uniform(-jitter_m, jitter_m),
            "z": base_position.get("z", 0.0),
        }

    def randomize_scale(self, base_scale: float, variation: float = 0.1) -> float:
        rng = self.get_rng("asset")
        return max(0.1, base_scale + rng.uniform(-variation, variation))

    def randomize_rotation(self, base_rotation: float, variation: float = 5.0) -> float:
        rng = self.get_rng("asset")
        return base_rotation + rng.uniform(-variation, variation)

    def randomization_report(self) -> Dict[str, Any]:
        return {
            "seeds": dict(self.seeds),
            "domains": list(self._rngs.keys()),
        }
