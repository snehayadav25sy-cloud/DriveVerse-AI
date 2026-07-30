"""
lidar.py — attach a LiDAR (ray-cast) sensor to the ego vehicle.

Sensor: sensor.lidar.ray_cast
Mount:  vehicle roof, centered (x=0, y=0, z=2.5)
Default spec (matches typical 32-channel HDL-32E profile):
    channels            = 32
    range               = 100 m
    rotation_frequency  = 10 Hz   (10 full scans per second)
    points_per_second   = 100 000 (≈3125 pts/channel/rotation at 10 Hz)
"""

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def attach_lidar(
    world,
    vehicle,
    channels: int = 32,
    range_m: float = 100.0,
    rotation_frequency: float = 10.0,
    points_per_second: int = 100_000,
):
    """
    Attach a CARLA LiDAR (ray_cast) sensor to *vehicle* and return the actor.

    Parameters
    ----------
    world               : carla.World
    vehicle             : carla.Vehicle  (ego vehicle actor)
    channels            : int            number of laser channels (beams)
    range_m             : float          max detection range in metres
    rotation_frequency  : float          rotations per second (Hz)
    points_per_second   : int            total points emitted per second across all channels

    Returns
    -------
    carla.Sensor  — the spawned LiDAR actor (caller must destroy it in finally)
    """
    blueprint_library = world.get_blueprint_library()
    lidar_bp = blueprint_library.find("sensor.lidar.ray_cast")

    lidar_bp.set_attribute("channels",            str(channels))
    lidar_bp.set_attribute("range",               str(range_m))
    lidar_bp.set_attribute("rotation_frequency",  str(rotation_frequency))
    lidar_bp.set_attribute("points_per_second",   str(points_per_second))

    # Roof-mount: directly above the vehicle's centre of mass
    # z=2.5 clears the vehicle roof on most CARLA car blueprints
    transform = _carla.Transform(
        _carla.Location(x=0.0, y=0.0, z=2.5),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    lidar = world.spawn_actor(lidar_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA LiDAR] Attached {channels}-ch LiDAR "
        f"(range={range_m}m, {rotation_frequency}Hz, {points_per_second}pps) "
        f"at {transform}"
    )
    return lidar
