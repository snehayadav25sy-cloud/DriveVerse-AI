"""
semantic_camera.py — attach a Semantic Segmentation Camera sensor to the ego vehicle.

Sensor: sensor.camera.semantic_segmentation
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

# CARLA / CityScapes official semantic color palette mapping tag_id -> (R, G, B)
CARLA_SEMANTIC_PALETTE = np.zeros((256, 3), dtype=np.uint8)
_DEFAULT_PALETTE = {
    0: (0, 0, 0),        # Unlabeled
    1: (70, 70, 70),     # Building
    2: (100, 40, 40),    # Fence
    3: (55, 90, 80),     # Other
    4: (220, 20, 60),    # Pedestrian
    5: (153, 153, 153),  # Pole
    6: (157, 234, 50),   # RoadLine
    7: (128, 64, 128),   # Road
    8: (244, 35, 232),   # Sidewalk
    9: (107, 142, 35),   # Vegetation
    10: (0, 0, 142),     # Vehicle
    11: (102, 102, 156), # Wall
    12: (220, 220, 0),   # TrafficSign
    13: (70, 130, 180),  # Sky
    14: (81, 0, 81),     # Ground
    15: (150, 100, 100), # Bridge
    16: (230, 150, 140), # RailTrack
    17: (180, 165, 180), # GuardRail
    18: (250, 170, 30),  # TrafficLight
    19: (110, 190, 160), # Static
    20: (170, 120, 50),  # Dynamic
    21: (45, 60, 150),   # Water
    22: (145, 170, 100), # Terrain
}
for tag, color in _DEFAULT_PALETTE.items():
    CARLA_SEMANTIC_PALETTE[tag] = color


def attach_semantic_camera(
    world,
    vehicle,
    width: int = 800,
    height: int = 600,
    fov: float = 90.0,
):
    """
    Attach a CARLA Semantic Segmentation Camera sensor to *vehicle* and return the actor.
    """
    blueprint_library = world.get_blueprint_library()
    sem_bp = blueprint_library.find("sensor.camera.semantic_segmentation")

    sem_bp.set_attribute("image_size_x", str(width))
    sem_bp.set_attribute("image_size_y", str(height))
    sem_bp.set_attribute("fov", str(fov))

    # Match RGB camera transform
    transform = _carla.Transform(
        _carla.Location(x=1.5, y=0.0, z=1.4),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    sem_cam = world.spawn_actor(sem_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA Semantic] Attached Semantic Camera ({width}x{height}, FOV={fov}°) at {transform}"
    )
    return sem_cam


def parse_carla_semantic(raw_data_bytes, width=800, height=600):
    """
    Parse raw CARLA semantic BGRA data into RGB image using official color palette.
    Tag ID is stored in the R channel (index 2 in BGRA).
    """
    bgra = np.frombuffer(raw_data_bytes, dtype=np.uint8).reshape((height, width, 4))
    tag_ids = bgra[:, :, 2]
    rgb = CARLA_SEMANTIC_PALETTE[tag_ids]
    return rgb
