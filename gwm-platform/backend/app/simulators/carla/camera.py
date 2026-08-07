"""
app/simulators/carla/camera.py — Build 5: CARLA camera wrapper

This is the ONLY allowed location for direct carla imports related to
camera operations. app/geography/ must never import carla directly.
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.simulators.carla.adapter import _carla


def attach_rgb_camera(world, vehicle, width: int = 1280, height: int = 720, fov: float = 90.0):
    """
    Attach an RGB camera to a vehicle.
    Returns the camera actor.
    """
    bp_lib = world.get_blueprint_library()
    bp = bp_lib.find("sensor.camera.rgb")
    bp.set_attribute("image_size_x", str(width))
    bp.set_attribute("image_size_y", str(height))
    bp.set_attribute("fov", str(fov))
    bp.set_attribute("sensor_tick", "0.1")

    transform = _carla.Transform(
        _carla.Location(x=1.5, y=0.0, z=1.4),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )
    return world.spawn_actor(bp, transform, attach_to=vehicle)


def make_transform(x: float, y: float, z: float, pitch: float = 0.0, yaw: float = 0.0, roll: float = 0.0):
    """Create a carla.Transform."""
    return _carla.Transform(
        _carla.Location(x=x, y=y, z=z),
        _carla.Rotation(pitch=pitch, yaw=yaw, roll=roll),
    )
