"""
app/sensor_realism/calibration.py — Build 6: Sensor calibration metadata
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np


def compute_intrinsic_matrix(
    width: int,
    height: int,
    fov_degrees: float,
) -> List[List[float]]:
    """Compute 3x3 camera intrinsic matrix K."""
    fov_rad = math.radians(fov_degrees)
    fx = width / (2.0 * math.tan(fov_rad / 2.0))
    fy = height / (2.0 * math.tan(fov_rad / 2.0))
    cx = width / 2.0
    cy = height / 2.0
    return [
        [fx, 0.0, cx],
        [0.0, fy, cy],
        [0.0, 0.0, 1.0],
    ]


def compute_extrinsic_matrix(
    position: Tuple[float, float, float],
    rotation_deg: Tuple[float, float, float],
) -> List[List[float]]:
    """Compute 4x4 extrinsic transform matrix from position and rotation (pitch, yaw, roll)."""
    pitch, yaw, roll = [math.radians(r) for r in rotation_deg]

    # Rotation matrices
    Rx = np.array([
        [1, 0, 0],
        [0, math.cos(pitch), -math.sin(pitch)],
        [0, math.sin(pitch), math.cos(pitch)],
    ])
    Ry = np.array([
        [math.cos(yaw), 0, math.sin(yaw)],
        [0, 1, 0],
        [-math.sin(yaw), 0, math.cos(yaw)],
    ])
    Rz = np.array([
        [math.cos(roll), -math.sin(roll), 0],
        [math.sin(roll), math.cos(roll), 0],
        [0, 0, 1],
    ])
    R = Rz @ Ry @ Rx

    # Translation
    t = np.array(position).reshape(3, 1)

    # 4x4 extrinsic
    extrinsic = np.eye(4)
    extrinsic[:3, :3] = R
    extrinsic[:3, 3] = t.flatten()
    return extrinsic.tolist()


def invert_extrinsic(extrinsic: List[List[float]]) -> List[List[float]]:
    """Invert a 4x4 extrinsic matrix."""
    E = np.array(extrinsic)
    R = E[:3, :3]
    t = E[:3, 3].reshape(3, 1)
    inv = np.eye(4)
    inv[:3, :3] = R.T
    inv[:3, 3] = (-R.T @ t).flatten()
    return inv.tolist()


def compute_camera_to_camera_transform(
    ext1: List[List[float]],
    ext2: List[List[float]],
) -> List[List[float]]:
    """Compute relative transform from camera 1 to camera 2."""
    E1 = np.array(ext1)
    E2 = np.array(ext2)
    return (E2 @ np.linalg.inv(E1)).tolist()
