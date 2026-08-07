"""
app/simulators/carla/carla_assets.py — Build 6: CARLA asset registry

Maps semantic asset references to CARLA blueprint library candidates.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


class CarlaAssetRegistry:
    """Resolves semantic assets to CARLA blueprints."""

    def __init__(self, world):
        self.world = world
        self.blueprint_library = world.get_blueprint_library() if _CARLA_AVAILABLE else None

    def resolve(self, asset_reference) -> Optional[Any]:
        """
        Resolve an AssetReference to a CARLA blueprint.
        Returns None if no match found.
        """
        if not _CARLA_AVAILABLE or self.blueprint_library is None:
            return None

        candidates = [asset_reference.resolved_asset_id] + asset_reference.fallback_chain
        for candidate in candidates:
            try:
                bp = self.blueprint_library.find(candidate)
                if bp is not None:
                    return bp
            except Exception:
                continue
        return None
