"""
capture/lidar.py — LiDAR point-cloud output handler.

Receives a numpy array of shape (N, 4) — columns: x, y, z, intensity —
and writes an ASCII PCD file to pointcloud/{frame:06d}.pcd.

PCD (Point Cloud Data) format is the standard for PCL, Open3D, and ROS.
ASCII encoding is used for universal compatibility without endian guesswork.

Design: no CARLA imports. The worker parses the raw CARLA buffer into a
plain float list/array before calling save_lidar().
"""

import os
import struct
from typing import List, Tuple


def save_lidar(
    points: List[Tuple[float, float, float, float]],
    frame_id: int,
    output_dir: str,
) -> str:
    """
    Write an ASCII PCD file for one LiDAR frame.

    Parameters
    ----------
    points     : list of (x, y, z, intensity) tuples or any iterable of 4-tuples.
    frame_id   : int  Zero-based frame index.
    output_dir : str  Root dataset directory; pointcloud/ sub-dir is created.

    Returns
    -------
    str  Absolute path of the written file.
    """
    pc_dir = os.path.join(output_dir, "pointcloud")
    os.makedirs(pc_dir, exist_ok=True)
    path = os.path.join(pc_dir, f"{frame_id:06d}.pcd")

    num_points = len(points)

    with open(path, "w") as f:
        # PCD ASCII header
        f.write("# .PCD v0.7 - Point Cloud Data file format\n")
        f.write("VERSION 0.7\n")
        f.write("FIELDS x y z intensity\n")
        f.write("SIZE 4 4 4 4\n")
        f.write("TYPE F F F F\n")
        f.write("COUNT 1 1 1 1\n")
        f.write(f"WIDTH {num_points}\n")
        f.write("HEIGHT 1\n")
        f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
        f.write(f"POINTS {num_points}\n")
        f.write("DATA ascii\n")
        # Point data
        for x, y, z, intensity in points:
            f.write(f"{x:.6f} {y:.6f} {z:.6f} {intensity:.6f}\n")

    return path


def parse_carla_lidar_raw(raw_bytes: bytes) -> List[Tuple[float, float, float, float]]:
    """
    Parse raw bytes from a CARLA LiDAR measurement into a list of (x,y,z,intensity).

    CARLA's LiDAR raw_data is a flat byte array of float32 quads:
        [x0, y0, z0, i0,  x1, y1, z1, i1, ...]

    This helper is called by the CARLA-side worker before handing data to
    dataset-engine/ — keeping the CARLA dependency boundary clean.
    """
    FLOAT_SIZE = 4
    STRIDE = 4 * FLOAT_SIZE
    points = []
    for offset in range(0, len(raw_bytes), STRIDE):
        if offset + STRIDE > len(raw_bytes):
            break
        x, y, z, intensity = struct.unpack_from("ffff", raw_bytes, offset)
        points.append((x, y, z, intensity))
    return points
