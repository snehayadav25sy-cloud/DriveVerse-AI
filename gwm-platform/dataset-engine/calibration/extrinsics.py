"""
calibration/extrinsics.py — camera ↔ LiDAR extrinsic transform.

In CARLA, the RGB camera and the LiDAR are both mounted at fixed offsets
relative to the ego vehicle. The extrinsic transform T_lidar_camera maps
a point from the camera frame into the LiDAR frame (and its inverse maps
from LiDAR → camera).

Sensor mount offsets (from worker/simulator/carla/):
  RGB camera : spawn_point relative to vehicle = (x=1.5, y=0, z=2.4)
               facing forward (pitch=0, yaw=0, roll=0)
  LiDAR      : spawn_point relative to vehicle = (x=0,   y=0, z=2.4)
               facing forward (pitch=0, yaw=0, roll=0)

Both sensors share the same Z height and forward orientation; the only
offset is the X translation of +1.5 m for the camera.

Output is a plain Python dict (JSON-serializable).
"""

import math


# Fixed mount positions relative to ego vehicle (in metres)
# Update these if the physical mount changes in camera.py / lidar.py.
CAMERA_MOUNT = {"x": 1.5, "y": 0.0, "z": 1.4, "pitch": 0.0, "yaw": 0.0, "roll": 0.0}
LIDAR_MOUNT  = {"x": 0.0, "y": 0.0, "z": 2.5, "pitch": 0.0, "yaw": 0.0, "roll": 0.0}


def compute_extrinsics() -> dict:
    """
    Compute the camera ↔ LiDAR extrinsic transform from fixed sensor mounts.

    Because both sensors have zero rotation offset and the only difference is
    an X translation of 1.5 m, the 4×4 homogeneous transform T_lidar_camera
    (camera-to-LiDAR) is a pure translation:

        T = [[1, 0, 0, -1.5],
             [0, 1, 0,  0.0],
             [0, 0, 1,  0.0],
             [0, 0, 0,  1.0]]

    Returns
    -------
    dict with keys:
        "T_cam_to_lidar" : list  4×4 homogeneous transform (row-major nested list)
        "T_lidar_to_cam" : list  4×4 inverse transform
        "camera_mount"   : dict  Camera mount offset from vehicle origin
        "lidar_mount"    : dict  LiDAR mount offset from vehicle origin
    """
    # Translation: camera is 1.5 m forward of LiDAR (same height)
    tx = LIDAR_MOUNT["x"] - CAMERA_MOUNT["x"]   # = -1.5
    ty = LIDAR_MOUNT["y"] - CAMERA_MOUNT["y"]   # = 0.0
    tz = LIDAR_MOUNT["z"] - CAMERA_MOUNT["z"]   # = 0.0

    T_cam_to_lidar = [
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0],
    ]

    # Inverse: negate the translation (rotation is identity)
    T_lidar_to_cam = [
        [1.0, 0.0, 0.0, -tx],
        [0.0, 1.0, 0.0, -ty],
        [0.0, 0.0, 1.0, -tz],
        [0.0, 0.0, 0.0,  1.0],
    ]

    return {
        "T_cam_to_lidar": T_cam_to_lidar,
        "T_lidar_to_cam": T_lidar_to_cam,
        "camera_mount":   CAMERA_MOUNT,
        "lidar_mount":    LIDAR_MOUNT,
    }
