"""
app/scenario_execution/sensors/sensor_manager.py — Build 7: Sensor manager

Manages sensor lifecycle and health.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import SensorState

logger = logging.getLogger(__name__)


class SensorManager:
    """Manages sensors for a simulation session."""

    def __init__(self):
        self._sensors: Dict[str, SensorState] = {}

    def register(self, sensor: SensorState) -> None:
        """Register a sensor."""
        self._sensors[sensor.sensor_id] = sensor
        logger.info(f"[SensorManager] Registered {sensor.sensor_id} ({sensor.sensor_type})")

    def unregister(self, sensor_id: str) -> bool:
        """Unregister a sensor."""
        if sensor_id in self._sensors:
            del self._sensors[sensor_id]
            return True
        return False

    def get_sensor(self, sensor_id: str) -> Optional[SensorState]:
        """Get sensor by ID."""
        return self._sensors.get(sensor_id)

    def get_all_sensors(self) -> List[SensorState]:
        """Get all registered sensors."""
        return list(self._sensors.values())

    def get_sensors_by_type(self, sensor_type: str) -> List[SensorState]:
        """Get sensors filtered by type."""
        return [s for s in self._sensors.values() if s.sensor_type == sensor_type]

    def mark_frame(self, sensor_id: str, frame_id: int) -> bool:
        """Mark a frame as captured for a sensor."""
        sensor = self._sensors.get(sensor_id)
        if sensor:
            sensor.frame_count += 1
            return True
        return False

    def health_check(self) -> Dict[str, bool]:
        """Check health of all sensors."""
        return {sid: s.healthy for sid, s in self._sensors.items()}

    def cleanup(self) -> None:
        """Unregister all sensors."""
        self._sensors.clear()
