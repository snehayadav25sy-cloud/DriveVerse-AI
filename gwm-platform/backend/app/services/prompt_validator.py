"""
prompt_validator.py — Build 3.2: Scenario Prompt Validator
============================================================
Validates a ScenarioConfig against CARLA engine limits and sensor
compatibility rules, producing a structured ValidationResult.

Rules produce three severity levels:
  ERROR   → validation_passed = False (job should be blocked)
  WARNING → validation_passed = True  (proceed with caution)
  INFO    → informational notes only
"""

from __future__ import annotations

from app.schemas.scenario import ScenarioConfig, ValidationIssue, ValidationResult


def validate_scenario(cfg: ScenarioConfig) -> ValidationResult:
    """
    Validate *cfg* against engine limits and sensor compatibility rules.

    Mutates *cfg* in-place:
      - cfg.validation_passed  → False if any ERROR is produced
      - cfg.validation         → the returned ValidationResult

    Returns the ValidationResult.
    """
    errors:   list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    infos:    list[ValidationIssue] = []

    total_vehicles = cfg.vehicles.total

    # ── Hard limits (ERROR) ───────────────────────────────────────────────────

    if total_vehicles > 500:
        errors.append(ValidationIssue(
            level="error",
            field="vehicles.total",
            message=f"Vehicle count {total_vehicles} exceeds engine limit (500)",
            value=total_vehicles,
            limit=500,
        ))

    if cfg.pedestrians > 200:
        errors.append(ValidationIssue(
            level="error",
            field="pedestrians",
            message=f"Pedestrian count {cfg.pedestrians} exceeds limit (200)",
            value=cfg.pedestrians,
            limit=200,
        ))

    if cfg.frames > 2000:
        errors.append(ValidationIssue(
            level="error",
            field="frames",
            message=f"Frame count {cfg.frames} exceeds engine limit (2000)",
            value=cfg.frames,
            limit=2000,
        ))

    if cfg.frames < 1:
        errors.append(ValidationIssue(
            level="error",
            field="frames",
            message=f"Frame count {cfg.frames} must be at least 1",
            value=cfg.frames,
            limit=1,
        ))

    if not cfg.sensors:
        errors.append(ValidationIssue(
            level="error",
            field="sensors",
            message="sensors list must not be empty; at least one sensor is required",
            value=cfg.sensors,
            limit=None,
        ))

    # ── Warnings ──────────────────────────────────────────────────────────────

    if len(cfg.sensors) >= 7:
        warnings.append(ValidationIssue(
            level="warning",
            field="sensors",
            message="7+ sensors may impact CARLA performance",
            value=len(cfg.sensors),
            limit=7,
        ))

    has_lidar = "lidar" in cfg.sensors
    has_rgb   = "rgb"   in cfg.sensors

    if has_lidar and not has_rgb:
        warnings.append(ValidationIssue(
            level="warning",
            field="sensors",
            message="LiDAR without RGB: calibration data will lack image reference",
            value=cfg.sensors,
            limit=None,
        ))

    if (
        total_vehicles == 0
        and cfg.traffic_density is not None
        and cfg.traffic_density != "None"
    ):
        warnings.append(ValidationIssue(
            level="warning",
            field="traffic_density",
            message="Traffic density set but no vehicles configured",
            value=cfg.traffic_density,
            limit=None,
        ))

    if total_vehicles > 200:
        warnings.append(ValidationIssue(
            level="warning",
            field="vehicles.total",
            message="High vehicle count may reduce CARLA frame rate",
            value=total_vehicles,
            limit=200,
        ))

    # ── Info ──────────────────────────────────────────────────────────────────

    if cfg.weather == "Fog" and has_lidar:
        infos.append(ValidationIssue(
            level="info",
            field="weather",
            message="Fog weather reduces LiDAR effective range to ~30m",
            value=cfg.weather,
            limit=None,
        ))

    # ── Assemble result ───────────────────────────────────────────────────────

    result = ValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        infos=infos,
    )

    # Mutate cfg in-place
    cfg.validation_passed = result.passed
    cfg.validation = result

    return result
