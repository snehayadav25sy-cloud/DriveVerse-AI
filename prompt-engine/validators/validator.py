"""
prompt-engine/validators/validator.py
=======================================
Build 3 — Phase 3: Plausibility validator

Applies semantic rules beyond basic schema validation.
Returns specific, human-readable rejection reasons — never generic errors.
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass, field
from typing import List
from schemas.scenario_schema import ScenarioConfig


# ── Rules tables ──────────────────────────────────────────────────────────────

# Maps with hot/dry climates — heavy snow is implausible
_DRY_CLIMATE_MAPS: frozenset[str] = frozenset({"Town01"})  # can extend per country

# Maps that represent highway-only / no-pedestrian zones
_NO_PEDESTRIAN_MAPS: frozenset[str] = frozenset({"Town06"})  # multi-lane only

# Maximum total vehicle count per map (Town06 big, Town01 smaller)
_MAP_VEHICLE_LIMITS: dict[str, int] = {
    "Town01": 200, "Town02": 150, "Town03": 300,
    "Town04": 250, "Town05": 350, "Town06": 500,
    "Town07": 100, "Town10HD": 400,
}

# Sensor combinations that are physically nonsensical
_INVALID_SENSOR_COMBOS: list[tuple[frozenset[str], str]] = [
    # optical_flow without any camera — no image to compute flow from
    (frozenset({"optical_flow"}), "rgb"),
    # instance segmentation without semantic — instance requires semantic pass
    (frozenset({"instance"}), "semantic"),
]

# Actor types that are not real vehicle categories (LLM hallucination check)
_INVALID_ACTOR_NAMES: frozenset[str] = frozenset({
    "airplane", "aircraft", "plane", "helicopter",
    "boat", "ship", "submarine", "rocket", "drone",
    "tank", "train", "spaceship",
})


@dataclass
class ValidationResult:
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def reject(self, reason: str) -> None:
        self.passed = False
        self.errors.append(reason)

    def warn(self, reason: str) -> None:
        self.warnings.append(reason)


def validate_scenario(cfg: ScenarioConfig, source_prompt: str = "") -> ValidationResult:
    """
    Run plausibility checks on a schema-valid ScenarioConfig.

    Rules applied:
    1. Heavy snow rejected for hot-climate maps (Dubai-profile)
    2. Pedestrians on highway-only maps
    3. Vehicle counts exceeding per-map limits
    4. Nonsensical actor types detected in prompt text
    5. Sensor combination physics (optical_flow without rgb, etc.)
    6. LiDAR + extreme fog warning
    """
    result = ValidationResult()
    prompt_lower = source_prompt.lower()

    # ── Rule 1: Snow in hot-climate / desert-profile scenarios ───────────────
    # Check weather label OR source prompt text
    heavy_snow_in_weather = cfg.weather.rain < 0.1 and cfg.weather.fog < 0.3 and \
                            ("snow" in prompt_lower or "blizzard" in prompt_lower or "snowstorm" in prompt_lower)
    if heavy_snow_in_weather and (
        ("dubai" in prompt_lower) or
        ("desert" in prompt_lower) or
        (cfg.city and cfg.city.lower() in {"dubai", "abu dhabi", "riyadh", "doha"}) or
        (cfg.country and cfg.country.lower() in {"uae", "saudi arabia", "qatar", "kuwait"})
    ):
        result.reject(
            "Scenario rejected: heavy snow is implausible in a desert / hot-climate location "
            f"(city={cfg.city}, country={cfg.country}). "
            "Dubai and similar locations have no recorded snowfall. "
            "Clarify whether you meant rain, fog, or dust storm instead."
        )

    # ── Rule 2: Pedestrians on highway-only maps ─────────────────────────────
    if cfg.map in _NO_PEDESTRIAN_MAPS and cfg.pedestrians > 0:
        result.reject(
            f"Scenario rejected: pedestrians ({cfg.pedestrians}) are not supported on "
            f"{cfg.map}, which is a highway-only multi-lane map with no walkable areas. "
            "Remove pedestrians or choose a different map."
        )

    # ── Rule 3: Vehicle count exceeds per-map limit ───────────────────────────
    map_limit = _MAP_VEHICLE_LIMITS.get(cfg.map, 300)
    if cfg.traffic.total > map_limit:
        result.reject(
            f"Scenario rejected: vehicle count ({cfg.traffic.total}) exceeds the "
            f"supported limit for {cfg.map} ({map_limit}). "
            "Reduce vehicle counts or choose a larger map (Town05 or Town10HD)."
        )

    # ── Rule 4: Nonsensical actor types in prompt ─────────────────────────────
    for actor in _INVALID_ACTOR_NAMES:
        if actor in prompt_lower:
            result.reject(
                f"Scenario rejected: '{actor}' is not a supported CARLA actor type. "
                "Supported vehicles: cars, trucks, buses, motorcycles, bicycles. "
                "Supported pedestrians: people on foot."
            )
            break   # one rejection is enough

    # ── Rule 5: Sensor combination physics ───────────────────────────────────
    sensor_set = frozenset(cfg.sensors)
    for (requires_extra, requires), label in [
        ((frozenset({"optical_flow"}), "rgb"), "optical_flow without rgb"),
        ((frozenset({"instance"}), "semantic"), "instance without semantic"),
    ]:
        if requires_extra.issubset(sensor_set) and requires not in sensor_set:
            result.reject(
                f"Sensor combination error: '{label}' is physically invalid. "
                f"optical_flow requires an RGB image source; "
                f"instance segmentation requires the semantic pass to be active."
            )

    # ── Rule 6: LiDAR performance degradation in heavy fog (warning only) ────
    if "lidar" in sensor_set and cfg.weather.fog > 0.6:
        result.warn(
            f"Warning: heavy fog (fog={cfg.weather.fog:.1f}) will severely reduce "
            "LiDAR effective range to approximately 15–30 m. "
            "Consider reducing fog density or adding a second sensor modality."
        )

    # ── Rule 7: All-zero weather but night request (lighting mismatch) ────────
    if (cfg.time_of_day and "night" in str(cfg.time_of_day).lower()) and \
            cfg.weather.cloudiness < 0.1:
        result.warn(
            "Note: night-time simulation with zero cloudiness will use full "
            "moon/streetlight lighting in CARLA. Add cloudiness > 0.5 for darker scenes."
        )

    return result
