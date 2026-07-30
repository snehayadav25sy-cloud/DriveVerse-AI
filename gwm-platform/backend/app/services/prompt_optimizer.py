"""
prompt_optimizer.py — Build 3.3: Scenario Prompt Optimizer
============================================================
Expands a sparse ScenarioConfig with intelligent contextual defaults
without overwriting values the user already provided (i.e. values whose
confidence score is > 0).

Each change is recorded as an OptimizerChange and stored on the config
so the frontend can show the user what was inferred vs. provided.
"""

from __future__ import annotations

from app.schemas.scenario import OptimizerChange, ScenarioConfig


def optimize_scenario(cfg: ScenarioConfig) -> ScenarioConfig:
    """
    Fill in missing fields on *cfg* using contextual expansion rules.

    Mutates *cfg* in-place:
      - cfg.optimizer_applied  → True
      - cfg.optimizer_changes  → list of OptimizerChange records

    Returns the mutated *cfg*.
    """
    changes: list[OptimizerChange] = []

    def _record(field: str, from_value, to_value, reason: str) -> None:
        changes.append(OptimizerChange(
            field=field,
            from_value=from_value,
            to_value=to_value,
            reason=reason,
        ))

    # ── Rule 1: Highway → default Medium traffic density ─────────────────────
    if cfg.road_type == "Highway" and cfg.traffic_density is None:
        _record("traffic_density", None, "Medium",
                "Highway roads typically have medium traffic flow")
        cfg.traffic_density = "Medium"

    # ── Rule 2: Highway → seed vehicle mix if none provided ──────────────────
    if cfg.road_type == "Highway" and cfg.vehicles.total == 0:
        _record("vehicles.car",   0, 80,  "Highway: seeding 80 cars")
        _record("vehicles.truck", 0, 20,  "Highway: seeding 20 trucks")
        cfg.vehicles.car   = 80
        cfg.vehicles.truck = 20

    # ── Rule 3: Night → artificial lighting ──────────────────────────────────
    if cfg.time_of_day == "Night" and cfg.lighting is None:
        _record("lighting", None, "Artificial",
                "Night simulation requires artificial lighting")
        cfg.lighting = "Artificial"

    # ── Rule 4: Fog + LiDAR → info note ──────────────────────────────────────
    if cfg.weather == "Fog" and "lidar" in cfg.sensors:
        changes.append(OptimizerChange(
            field="sensors",
            from_value="lidar",
            to_value="lidar",
            reason="INFO: Fog reduces LiDAR to ~30m — consider adding RGB for cross-validation",
        ))

    # ── Rule 5: Heavy traffic → seed vehicle mix ──────────────────────────────
    if cfg.traffic_density == "Heavy" and cfg.vehicles.total == 0:
        _record("vehicles.car",        0, 150, "Heavy traffic: seeding 150 cars")
        _record("vehicles.truck",      0,  30, "Heavy traffic: seeding 30 trucks")
        _record("vehicles.motorcycle", 0,  20, "Heavy traffic: seeding 20 motorcycles")
        cfg.vehicles.car        = 150
        cfg.vehicles.truck      = 30
        cfg.vehicles.motorcycle = 20

    # ── Rule 6: Light traffic → seed vehicle mix ──────────────────────────────
    if cfg.traffic_density == "Light" and cfg.vehicles.total == 0:
        _record("vehicles.car", 0, 20, "Light traffic: seeding 20 cars")
        cfg.vehicles.car = 20

    # ── Rule 7: Medium traffic → seed vehicle mix ─────────────────────────────
    if cfg.traffic_density == "Medium" and cfg.vehicles.total == 0:
        _record("vehicles.car",   0, 60, "Medium traffic: seeding 60 cars")
        _record("vehicles.truck", 0, 10, "Medium traffic: seeding 10 trucks")
        cfg.vehicles.car   = 60
        cfg.vehicles.truck = 10

    # ── Rule 8: No weather → default Clear ───────────────────────────────────
    if cfg.weather is None:
        _record("weather", None, "Clear", "No weather specified; defaulting to Clear")
        cfg.weather = "Clear"

    # ── Rule 9: No time_of_day → default Day ─────────────────────────────────
    if cfg.time_of_day is None:
        _record("time_of_day", None, "Day", "No time of day specified; defaulting to Day")
        cfg.time_of_day = "Day"

    # ── Rule 10: No traffic AND no vehicles → Medium + seed mix ──────────────
    if cfg.traffic_density is None and cfg.vehicles.total == 0:
        _record("traffic_density", None, "Medium",
                "No traffic density or vehicles specified; defaulting to Medium")
        _record("vehicles.car",   0, 60, "Medium traffic default: seeding 60 cars")
        _record("vehicles.truck", 0, 10, "Medium traffic default: seeding 10 trucks")
        cfg.traffic_density = "Medium"
        cfg.vehicles.car   = 60
        cfg.vehicles.truck = 10

    cfg.optimizer_applied = True
    cfg.optimizer_changes = changes
    return cfg
