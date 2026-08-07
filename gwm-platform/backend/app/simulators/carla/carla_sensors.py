"""
app/simulators/carla/carla_sensors.py — Build 6: CARLA sensor realism application
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def attach_rgb_sensor(world, vehicle, sensor_config) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    try:
        bp = world.get_blueprint_library().find("sensor.camera.rgb")
        if sensor_config.resolution:
            bp.set_attribute("image_size_x", str(sensor_config.resolution[0]))
            bp.set_attribute("image_size_y", str(sensor_config.resolution[1]))
        if sensor_config.fov:
            bp.set_attribute("fov", str(sensor_config.fov))
        transform = _carla.Transform(
            _carla.Location(x=sensor_config.position.x, y=sensor_config.position.y, z=sensor_config.position.z),
            _carla.Rotation(*sensor_config.rotation),
        )
        return world.spawn_actor(bp, transform, attach_to=vehicle)
    except Exception as e:
        logger.warning(f"Failed to attach RGB sensor: {e}")
        return None


def attach_lidar_sensor(world, vehicle, sensor_config) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    try:
        bp = world.get_blueprint_library().find("sensor.lidar.ray_cast")
        transform = _carla.Transform(
            _carla.Location(x=sensor_config.position.x, y=sensor_config.position.y, z=sensor_config.position.z),
            _carla.Rotation(*sensor_config.rotation),
        )
        return world.spawn_actor(bp, transform, attach_to=vehicle)
    except Exception as e:
        logger.warning(f"Failed to attach LiDAR sensor: {e}")
        return None


def attach_radar_sensor(world, vehicle, sensor_config) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    try:
        bp = world.get_blueprint_library().find("sensor.other.radar")
        transform = _carla.Transform(
            _carla.Location(x=sensor_config.position.x, y=sensor_config.position.y, z=sensor_config.position.z),
            _carla.Rotation(*sensor_config.rotation),
        )
        return world.spawn_actor(bp, transform, attach_to=vehicle)
    except Exception as e:
        logger.warning(f"Failed to attach Radar sensor: {e}")
        return None


def attach_depth_sensor(world, vehicle, sensor_config) -> Optional[Any]:
    if not _CARLA_AVAILABLE:
        return None
    try:
        bp = world.get_blueprint_library().find("sensor.camera.depth")
        if sensor_config.resolution:
            bp.set_attribute("image_size_x", str(sensor_config.resolution[0]))
            bp.set_attribute("image_size_y", str(sensor_config.resolution[1]))
        transform = _carla.Transform(
            _carla.Location(x=sensor_config.position.x, y=sensor_config.position.y, z=sensor_config.position.z),
            _carla.Rotation(*sensor_config.rotation),
        )
        return world.spawn_actor(bp, transform, attach_to=vehicle)
    except Exception as e:
        logger.warning(f"Failed to attach Depth sensor: {e}")
        return None
