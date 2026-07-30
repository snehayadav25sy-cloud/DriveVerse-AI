"""
metadata/frame_metadata.py — per-frame JSON metadata writer.

Writes metadata/{frame:06d}.json containing:
  - weather conditions (from CARLA WeatherParameters)
  - simulation timestamp and CARLA tick number
  - ego vehicle speed (m/s)
  - GPS position (lat, lon, alt) if available
  - town / map name
  - sensors present in this frame

Design: no CARLA imports. All inputs are plain Python dicts/scalars.
"""

import os
import json
from datetime import datetime, timezone


def write_frame_metadata(
    frame_id: int,
    tick_number: int,
    output_dir: str,
    *,
    weather: dict = None,
    speed_ms: float = 0.0,
    gps: dict = None,
    town: str = "unknown",
    sensors_present: list = None,
    sim_elapsed_seconds: float = 0.0,
) -> str:
    """
    Write per-frame metadata as JSON.

    Parameters
    ----------
    frame_id            : int    Zero-based frame index (used in filename).
    tick_number         : int    CARLA simulation tick (shared across sensors).
    output_dir          : str    Root dataset directory.
    weather             : dict   {"cloudiness", "precipitation", "fog_density",
                                  "wind_intensity", "sun_altitude_angle", ...}
    speed_ms            : float  Ego vehicle speed in m/s.
    gps                 : dict   {"latitude", "longitude", "altitude"}
    town                : str    CARLA map/town name.
    sensors_present     : list   e.g. ["rgb", "lidar"]
    sim_elapsed_seconds : float  Cumulative simulation time in seconds.

    Returns
    -------
    str  Absolute path of the written JSON file.
    """
    meta_dir = os.path.join(output_dir, "metadata")
    os.makedirs(meta_dir, exist_ok=True)
    path = os.path.join(meta_dir, f"{frame_id:06d}.json")

    payload = {
        "frame_id":             frame_id,
        "tick_number":          tick_number,
        "sim_elapsed_seconds":  sim_elapsed_seconds,
        "wall_timestamp":       datetime.now(timezone.utc).isoformat(),
        "town":                 town,
        "sensors_present":      sensors_present or [],
        "ego_speed_ms":         speed_ms,
        "gps":                  gps or {"latitude": 0.0, "longitude": 0.0, "altitude": 0.0},
        "weather":              weather or {
            "cloudiness":         0.0,
            "precipitation":      0.0,
            "precipitation_deposits": 0.0,
            "wind_intensity":     0.0,
            "sun_azimuth_angle":  0.0,
            "sun_altitude_angle": 45.0,
            "fog_density":        0.0,
            "fog_distance":       0.0,
            "wetness":            0.0,
        },
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    return path
