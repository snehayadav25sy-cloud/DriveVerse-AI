"""
app/scenario_execution/deployment/map_deployer.py — Build 7: Map deployment abstraction

Formalizes the Build 5/6 OpenDRIVE limitation.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Dict, List, Optional

from app.scenario_execution.models import MapConfig, MapDeploymentStatus


class MapDeploymentResult(BaseModel):
    status: MapDeploymentStatus
    map_name: str
    instructions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class MapDeployer:
    """Handles map deployment for simulation."""

    def __init__(self, carla_maps_dir: Optional[str] = None):
        self.carla_maps_dir = carla_maps_dir or os.environ.get("CARLA_MAPS_DIR", "")

    def resolve(self, map_config: MapConfig) -> MapDeploymentResult:
        """Resolve map availability."""
        if map_config.provider == MapProviderType.TOWN:
            return MapDeploymentResult(
                status=MapDeploymentStatus.AVAILABLE,
                map_name=map_config.map_name,
                instructions=[],
            )

        if map_config.provider == MapProviderType.OPENDRIVE_ARTIFACT:
            artifact_path = map_config.artifact_path or ""
            if not os.path.exists(artifact_path):
                return MapDeploymentResult(
                    status=MapDeploymentStatus.UNAVAILABLE,
                    map_name=map_config.map_name,
                    error=f"OpenDRIVE artifact not found: {artifact_path}",
                )

            instructions = [
                f"Copy {artifact_path} to CARLA's Maps/ directory",
                f"Rename to {map_config.map_name}.xodr",
                "Restart CARLA with: -map={map_config.map_name}",
            ]

            return MapDeploymentResult(
                status=MapDeploymentStatus.DEPLOYMENT_REQUIRED,
                map_name=map_config.map_name,
                instructions=instructions,
            )

        return MapDeploymentResult(
            status=MapDeploymentStatus.UNAVAILABLE,
            map_name=map_config.map_name,
            error=f"Unknown map provider: {map_config.provider}",
        )
