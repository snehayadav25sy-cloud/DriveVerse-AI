"""
app/simulators/carla/carla_traffic.py — Build 6: CARLA traffic sign and light placement
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def place_traffic_sign(world, sign_plan, registry) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    bp = registry.resolve(sign_plan.asset) if sign_plan.asset else None
    if bp is None:
        logger.warning(f"No blueprint for sign {sign_plan.sign_id}")
        return None
    try:
        transform = _carla.Transform(
            _carla.Location(x=sign_plan.position.x, y=sign_plan.position.y, z=sign_plan.position.z),
            _carla.Rotation(yaw=sign_plan.rotation_deg),
        )
        return world.spawn_actor(bp, transform)
    except Exception as e:
        logger.warning(f"Failed to place sign {sign_plan.sign_id}: {e}")
        return None


def place_traffic_light(world, tl_plan, registry) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    bp = registry.resolve(tl_plan.asset) if tl_plan.asset else None
    if bp is None:
        logger.warning(f"No blueprint for traffic light {tl_plan.traffic_light_id}")
        return None
    try:
        transform = _carla.Transform(
            _carla.Location(x=tl_plan.position.x, y=tl_plan.position.y, z=tl_plan.position.z),
            _carla.Rotation(yaw=tl_plan.rotation_deg),
        )
        return world.spawn_actor(bp, transform)
    except Exception as e:
        logger.warning(f"Failed to place traffic light {tl_plan.traffic_light_id}: {e}")
        return None
