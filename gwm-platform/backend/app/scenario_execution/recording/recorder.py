"""
app/scenario_execution/recording/recorder.py — Build 7: Recording engine

Output:
  dataset/
      rgb/
      lidar/
      radar/
      depth/
      semantic/
      instance/
      optical_flow/
      annotations/
      metadata/
      provenance/
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import RecordingManifest, FrameIndexEntry


class RecordingEngine:
    """Manages dataset recording during simulation."""

    def __init__(self, output_directory: str, session_id: str):
        self.output_directory = output_directory
        self.session_id = session_id
        self.manifest = RecordingManifest(
            session_id=session_id,
            frame_count=0,
            sensors=[],
            output_directory=output_directory,
        )
        self.frame_index: List[FrameIndexEntry] = []
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directory structure."""
        subdirs = [
            "rgb", "lidar", "radar", "depth", "semantic", "instance", "optical_flow",
            "annotations", "metadata", "provenance",
        ]
        for subdir in subdirs:
            os.makedirs(os.path.join(self.output_directory, subdir), exist_ok=True)

    def initialize(self, sensors: List[str]) -> None:
        """Initialize recording with sensor list."""
        self.manifest.sensors = list(sensors)

    def record_frame(self, frame_id: int, frame_data: Dict[str, Any]) -> None:
        """Record a single frame."""
        entry = FrameIndexEntry(frame_id=frame_id)
        for sensor_type in self.manifest.sensors:
            if sensor_type in frame_data:
                entry.__dict__[sensor_type] = frame_data[sensor_type]
        self.frame_index.append(entry)
        self.manifest.frame_count = len(self.frame_index)
        self.manifest.end_frame = frame_id

    def finalize(self) -> RecordingManifest:
        """Finalize recording and write manifest."""
        self.manifest.complete = True
        self._write_manifest()
        self._write_frame_index()
        return self.manifest

    def _write_manifest(self) -> None:
        path = os.path.join(self.output_directory, "manifest.json")
        with open(path, "w") as f:
            f.write(self.manifest.model_dump_json(indent=2))

    def _write_frame_index(self) -> None:
        path = os.path.join(self.output_directory, "frame_index.json")
        data = {str(entry.frame_id): entry.model_dump() for entry in self.frame_index}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def get_output_directory(self) -> str:
        return self.output_directory
