"""
app/simulators/carla/carla_spawn.py — Build 6: CARLA spawn helpers
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


def spawn_actor(world, blueprint, transform, attach_to=None) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    try:
        if attach_to:
            return world.spawn_actor(blueprint, transform, attach_to=attach_to)
        return world.spawn_actor(blueprint, transform)
    except Exception as e:
        logger.warning(f"Failed to spawn actor: {e}")
        return None


def destroy_actors(world, actors: List[Any]) -> None:
    if not _CARLA_AVAILABLE:
        return
    for actor in actors:
        try:
            if actor is not None and actor.is_alive:
                actor.destroy()
        except Exception:
            pass
