"""
app/scenario_execution/preflight.py — Build 7: Pre-flight validation

Validates all prerequisites before launching CARLA.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import (
    ExecutionPreflightReport,
    ExecutionSession,
    PreflightCheck,
)


class PreflightValidator:
    """Validates execution session prerequisites."""

    def __init__(self, session: ExecutionSession):
        self.session = session
        self.checks: List[PreflightCheck] = []

    def validate(self) -> ExecutionPreflightReport:
        """Run all preflight checks."""
        self.checks = []
        errors: List[str] = []
        warnings: List[str] = []

        self._check_simulation_parameters()
        self._check_seeds()
        self._check_actors()
        self._check_sensors()
        self._check_events()
        self._check_output_directory()
        self._check_map_configuration()

        for check in self.checks:
            if not check.passed:
                errors.append(check.message or f"Check failed: {check.name}")
            elif check.message:
                warnings.append(check.message)

        passed = len(errors) == 0
        return ExecutionPreflightReport(
            passed=passed,
            errors=errors,
            warnings=warnings,
            checks=list(self.checks),
        )

    def _check_simulation_parameters(self):
        timing = self.session.timing
        if timing.fixed_delta_seconds <= 0:
            self.checks.append(PreflightCheck(
                name="timing",
                passed=False,
                message="fixed_delta_seconds must be > 0",
            ))
        elif timing.fixed_delta_seconds > 0.5:
            self.checks.append(PreflightCheck(
                name="timing",
                passed=True,
                message="fixed_delta_seconds is large, simulation may be slow",
            ))
        else:
            self.checks.append(PreflightCheck(name="timing", passed=True))

        if timing.total_simulation_seconds <= 0:
            self.checks.append(PreflightCheck(
                name="total_simulation_seconds",
                passed=False,
                message="total_simulation_seconds must be > 0",
            ))
        else:
            self.checks.append(PreflightCheck(name="total_simulation_seconds", passed=True))

    def _check_seeds(self):
        seeds = self.session.seeds
        required = ["master_seed", "traffic_seed", "spawn_seed", "event_seed", "weather_seed", "sensor_seed"]
        missing = [s for s in required if s not in seeds]
        if missing:
            self.checks.append(PreflightCheck(
                name="seeds",
                passed=False,
                message=f"Missing seeds: {missing}",
            ))
        else:
            self.checks.append(PreflightCheck(name="seeds", passed=True))

    def _check_actors(self):
        actors = self.session.actors
        if len(actors) == 0:
            self.checks.append(PreflightCheck(
                name="actors",
                passed=False,
                message="At least one actor is required",
            ))
        else:
            self.checks.append(PreflightCheck(name="actors", passed=True, message=f"{len(actors)} actors planned"))

    def _check_sensors(self):
        sensors = self.session.sensors
        if len(sensors) == 0:
            self.checks.append(PreflightCheck(
                name="sensors",
                passed=False,
                message="At least one sensor is required",
            ))
        else:
            self.checks.append(PreflightCheck(name="sensors", passed=True, message=f"{len(sensors)} sensors planned"))

    def _check_events(self):
        events = self.session.events
        self.checks.append(PreflightCheck(
            name="events",
            passed=True,
            message=f"{len(events)} events planned",
        ))

    def _check_output_directory(self):
        output_dir = self.session.recording.get("output_directory", "")
        if not output_dir:
            self.checks.append(PreflightCheck(
                name="output_directory",
                passed=False,
                message="output_directory is not set",
            ))
        else:
            os.makedirs(output_dir, exist_ok=True)
            self.checks.append(PreflightCheck(name="output_directory", passed=True))

    def _check_map_configuration(self):
        map_config = self.session.map
        if map_config.deployment_required:
            self.checks.append(PreflightCheck(
                name="map",
                passed=False,
                message=f"Map deployment required: {map_config.deployment_instructions}",
            ))
        else:
            self.checks.append(PreflightCheck(name="map", passed=True, message=f"Map {map_config.map_name} available"))
