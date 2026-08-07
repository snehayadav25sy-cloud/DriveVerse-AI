"""
app/scenario_execution/sensors/synchronization.py — Build 7: Sensor synchronization

Ensures all sensors capture synchronized frames.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.scenario_execution.models import SynchronizationReport


class SensorSynchronizer:
    """Validates sensor frame synchronization."""

    def __init__(self, sensor_ids: List[str]):
        self.sensor_ids = sensor_ids
        self.frame_records: Dict[int, Dict[str, Any]] = {}

    def record_frame(self, frame_id: int, sensor_id: str, timestamp: float) -> None:
        """Record a captured frame."""
        if frame_id not in self.frame_records:
            self.frame_records[frame_id] = {}
        self.frame_records[frame_id][sensor_id] = {
            "timestamp": timestamp,
            "present": True,
        }

    def validate(self) -> SynchronizationReport:
        """Validate synchronization across all sensors."""
        total_frames = len(self.frame_records)
        missing_sensor_frames: Dict[str, List[int]] = {sid: [] for sid in self.sensor_ids}
        duplicate_frames: List[int] = []
        out_of_order_frames: List[int] = []
        max_drift = 0.0

        for frame_id in sorted(self.frame_records.keys()):
            frame_data = self.frame_records[frame_id]
            timestamps = [v["timestamp"] for v in frame_data.values()]
            if len(timestamps) > 1:
                drift = max(timestamps) - min(timestamps)
                max_drift = max(max_drift, drift)

            for sensor_id in self.sensor_ids:
                if sensor_id not in frame_data:
                    missing_sensor_frames[sensor_id].append(frame_id)

        synchronized = all(len(v) == 0 for v in missing_sensor_frames.values())

        return SynchronizationReport(
            synchronized=synchronized,
            total_frames=total_frames,
            missing_sensor_frames=missing_sensor_frames,
            duplicate_frames=duplicate_frames,
            out_of_order_frames=out_of_order_frames,
            timestamp_drift_s=max_drift,
        )

    def reset(self) -> None:
        """Reset frame records."""
        self.frame_records.clear()
