"""
radar.py — attach a Radar sensor to the ego vehicle.

Sensor: sensor.other.radar
Mount:  front bumper, facing forward
        x=2.5 (forward), y=0 (centred), z=0.5 (bumper height)
Default spec:
    horizontal_fov  = 30°   (±15° around the vehicle's forward axis)
    vertical_fov    = 10°   (±5°, consistent with automotive radar spec)
    range_m         = 100   metres
"""

try:
    import carla as _carla
    _CARLA_AVAILABLE = True
except ImportError:
    _carla = None
    _CARLA_AVAILABLE = False


def attach_radar(
    world,
    vehicle,
    horizontal_fov: float = 30.0,
    vertical_fov:   float = 10.0,
    range_m:        float = 100.0,
):
    """
    Attach a CARLA Radar sensor to *vehicle* and return the actor.

    Parameters
    ----------
    world           : carla.World
    vehicle         : carla.Vehicle  (ego vehicle actor)
    horizontal_fov  : float          total horizontal field of view in degrees
    vertical_fov    : float          total vertical field of view in degrees
    range_m         : float          max detection range in metres

    Returns
    -------
    carla.Sensor  — the spawned Radar actor (caller must destroy it in finally)
    """
    blueprint_library = world.get_blueprint_library()
    radar_bp = blueprint_library.find("sensor.other.radar")

    radar_bp.set_attribute("horizontal_fov",  str(horizontal_fov))
    radar_bp.set_attribute("vertical_fov",    str(vertical_fov))
    radar_bp.set_attribute("range",           str(range_m))

    # Front-bumper mount, facing straight ahead (no pitch/yaw offset needed)
    transform = _carla.Transform(
        _carla.Location(x=2.5, y=0.0, z=0.5),
        _carla.Rotation(pitch=0.0, yaw=0.0, roll=0.0),
    )

    radar = world.spawn_actor(radar_bp, transform, attach_to=vehicle)
    print(
        f"[CARLA Radar] Attached Radar "
        f"(hFOV={horizontal_fov}°, vFOV={vertical_fov}°, range={range_m}m) "
        f"at {transform}"
    )
    return radar
