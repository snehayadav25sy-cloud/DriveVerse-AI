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

    CARLA 0.9.16 OpenDRIVE loading strategies (in order):
      1. Dynamic: client.generate_opendrive_world(xodr_content, params)
      2. Static: copy .xodr to CARLA Maps/ dir, then client.load_world(map_name)
      3. Fallback: load closest built-in CARLA town
    """

    def __init__(self, xodr_path: str):
        self.xodr_path = xodr_path
        self._map_name = os.path.basename(xodr_path).replace(".xodr", "")
        self._load_method: Optional[str] = None

    def prepare(self, map_artifact: Dict[str, Any]) -> MapProviderState:
        if not os.path.exists(self.xodr_path):
            logger.error(f"OpenDRIVE file not found: {self.xodr_path}")
            return MapProviderState.FAILED
        if not _CARLA_AVAILABLE:
            return MapProviderState.UNSUPPORTED
        # Try dynamic first; if unavailable, fall back to static deployment
        try:
            import carla as _carla
            _carla.OpendriveGenerationParameters
            return MapProviderState.READY
        except AttributeError:
            logger.warning(
                "CARLA 0.9.16 does not expose OpendriveGenerationParameters. "
                "Falling back to static Maps/ directory deployment."
            )
            return MapProviderState.DEPLOYMENT_REQUIRED

    def load(self, client):
        if not _CARLA_AVAILABLE:
            raise RuntimeError("CARLA not available")

        from app.simulators.carla.map_loader import load_opendrive_map
        result = load_opendrive_map(self.xodr_path)

        if not result["success"]:
            raise RuntimeError(
                f"Failed to load OpenDRIVE map: {result.get('error', 'unknown')}. "
                f"Detail: {result.get('detail', 'none')}"
            )

        self._load_method = result.get("load_method")
        return result
