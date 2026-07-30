"""
instance_camera.py — attach an Instance Segmentation Camera sensor to the ego vehicle.

Sensor: sensor.camera.instance_segmentation
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


def attach_instance_camera(
    world,
    vehicle,
    width: int = 800,
    height: int = 600,
    fov: float = 90.0,
):
    """
    Attach a CARLA Instance Segmentation Camera sensor to *vehicle* and return the actor.
    """
    blueprint_library = world.get_blueprint_library()
    inst_bp = blueprint_library.find("sensor.camera.instance_segmentation")

    inst_bp.set_attribute("image_size_x", str(width))
    inst_bp.set_attribute("image_size_y", str(height))
    inst_bp.set_attribute("fov", str(fov))

    # Match RGB camera transform
    transform = _carla.Transform(
        _carla.Location(x=1.5, y=0.0, z=1.4),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    inst_cam = world.spawn_actor(inst_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA Instance] Attached Instance Camera ({width}x{height}, FOV={fov}°) at {transform}"
    )
    return inst_cam


def parse_carla_instance(raw_data_bytes, width=800, height=600):
    """
    Parse raw CARLA instance BGRA data into deterministic RGB visualization.
    G and B channels contain the 16-bit actor instance ID.
    Mapping actor_id to deterministic color ensures identical actor IDs retain identical colors across frames.
    """
    bgra = np.frombuffer(raw_data_bytes, dtype=np.uint8).reshape((height, width, 4))
    b = bgra[:, :, 0].astype(np.uint32)
    g = bgra[:, :, 1].astype(np.uint32)
    
    actor_ids = g + (b << 8)

    # Deterministic RGB color for each actor_id
    r_color = ((actor_ids * 53) % 251).astype(np.uint8)
    g_color = ((actor_ids * 97) % 251).astype(np.uint8)
    b_color = ((actor_ids * 193) % 251).astype(np.uint8)

    rgb = np.stack([r_color, g_color, b_color], axis=-1)
    # Background / Unlabeled (actor_id == 0) remains black
    rgb[actor_ids == 0] = [0, 0, 0]
    return rgb, actor_ids
