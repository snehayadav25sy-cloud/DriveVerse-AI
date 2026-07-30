"""
depth_camera.py — attach a Depth Camera sensor to the ego vehicle.

Sensor: sensor.camera.depth
Mount:  same transform as RGB camera (x=1.5, y=0.0, z=1.4)
Resolution: 800x600 (deliberately lower than RGB 1280x720 to manage VRAM)
FOV: 90 degrees
"""

import numpy as np

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def attach_depth_camera(
    world,
    vehicle,
    width: int = 800,
    height: int = 600,
    fov: float = 90.0,
):
    """
    Attach a CARLA Depth Camera sensor to *vehicle* and return the actor.
    """
    blueprint_library = world.get_blueprint_library()
    depth_bp = blueprint_library.find("sensor.camera.depth")

    depth_bp.set_attribute("image_size_x", str(width))
    depth_bp.set_attribute("image_size_y", str(height))
    depth_bp.set_attribute("fov", str(fov))

    # Match RGB camera transform
    transform = _carla.Transform(
        _carla.Location(x=1.5, y=0.0, z=1.4),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    depth_cam = world.spawn_actor(depth_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA Depth] Attached Depth Camera ({width}x{height}, FOV={fov}°) at {transform}"
    )
    return depth_cam


def parse_carla_depth(raw_data_bytes, width=800, height=600):
    """
    Parse raw CARLA depth BGRA data into depth in meters (float32 array).
    Formula: (R + G * 256 + B * 256^2) / (256^3 - 1) * 1000.0
    """
    bgra = np.frombuffer(raw_data_bytes, dtype=np.uint8).reshape((height, width, 4))
    b = bgra[:, :, 0].astype(np.float32)
    g = bgra[:, :, 1].astype(np.float32)
    r = bgra[:, :, 2].astype(np.float32)

    normalized = (r + g * 256.0 + b * 65536.0) / 16777215.0
    depth_meters = normalized * 1000.0
    return depth_meters
