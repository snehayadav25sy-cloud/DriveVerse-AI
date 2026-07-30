"""
optical_flow.py — attach an Optical Flow Camera sensor to the ego vehicle.

Sensor: sensor.camera.optical_flow
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


def attach_optical_flow(
    world,
    vehicle,
    width: int = 800,
    height: int = 600,
    fov: float = 90.0,
):
    """
    Attach a CARLA Optical Flow Camera sensor to *vehicle* and return the actor.
    """
    blueprint_library = world.get_blueprint_library()
    flow_bp = blueprint_library.find("sensor.camera.optical_flow")

    flow_bp.set_attribute("image_size_x", str(width))
    flow_bp.set_attribute("image_size_y", str(height))
    flow_bp.set_attribute("fov", str(fov))

    # Match RGB camera transform
    transform = _carla.Transform(
        _carla.Location(x=1.5, y=0.0, z=1.4),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    flow_cam = world.spawn_actor(flow_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA OpticalFlow] Attached Optical Flow Camera ({width}x{height}, FOV={fov}°) at {transform}"
    )
    return flow_cam


def parse_carla_optical_flow(raw_data_bytes, width=800, height=600):
    """
    Parse raw CARLA optical flow bytes into (height, width, 2) float32 array (u, v motion vectors).
    In CARLA optical flow, raw_data contains float32 pairs (u, v) per pixel.
    """
    flow = np.frombuffer(raw_data_bytes, dtype=np.float32).reshape((height, width, 2))
    return flow
