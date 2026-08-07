"""
app/simulators/carla/map_provider.py — Build 6: CARLA map provider abstraction

Explicit map loading states:
  READY
  DEPLOYMENT_REQUIRED
  UNSUPPORTED
  FAILED
"""

from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


class MapProviderState(Enum):
    READY = "ready"
    DEPLOYMENT_REQUIRED = "deployment_required"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class MapProvider:
    """Base map provider interface."""

    def prepare(self, map_artifact: Dict[str, Any]) -> MapProviderState:
        raise NotImplementedError

    def load(self, client) -> Any:
        raise NotImplementedError


class ExistingCarlaMapProvider(MapProvider):
    """Loads an existing CARLA Town map."""

    def prepare(self, map_artifact: Dict[str, Any]) -> MapProviderState:
        map_name = map_artifact.get("carla_map_name", "Town01")
        if _CARLA_AVAILABLE:
            return MapProviderState.READY
        return MapProviderState.UNSUPPORTED

    def load(self, client):
        if not _CARLA_AVAILABLE:
            raise RuntimeError("CARLA not available")
        map_name = self._map_name
        return client.load_world(map_name)


class OpenDriveArtifactProvider(MapProvider):
    """
    Handles Build 5 generated OpenDRIVE artifacts.

    Preserves the known Build 5 gap:
    CARLA 0.9.16 does not dynamically load OpenDRIVE from Python.
    """

    def __init__(self, xodr_path: str):
        self.xodr_path = xodr_path
        self._map_name = os.path.basename(xodr_path).replace(".xodr", "")

    def prepare(self, map_artifact: Dict[str, Any]) -> MapProviderState:
        if not os.path.exists(self.xodr_path):
            logger.error(f"OpenDRIVE file not found: {self.xodr_path}")
            return MapProviderState.FAILED
        if not _CARLA_AVAILABLE:
            return MapProviderState.UNSUPPORTED
        # Build 5 known gap: dynamic loading not supported in 0.9.16
        logger.warning(
            "Build 5 OpenDRIVE artifact detected. "
            "CARLA 0.9.16 does not support dynamic OpenDRIVE loading via Python. "
            f"Map must be placed in CARLA Maps/ directory and CARLA restarted with -map={self._map_name}"
        )
        return MapProviderState.DEPLOYMENT_REQUIRED

    def load(self, client):
        raise RuntimeError(
            "OpenDRIVE dynamic loading is not supported in CARLA 0.9.16. "
            f"Place {self.xodr_path} in CARLA's Maps/ directory and restart CARLA with -map={self._map_name}"
        )
