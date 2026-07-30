"""
calibration/intrinsics.py — camera intrinsic matrix computation.

Computes the 3×3 intrinsic matrix K from camera FOV and image dimensions.
Assumes a standard pinhole camera model with square pixels and centred
principal point (CARLA's default camera model).

Output is a plain Python dict (JSON-serializable) — no numpy required.
"""

import math


def compute_intrinsics(
    image_width: int,
    image_height: int,
    fov_h_degrees: float = 90.0,
) -> dict:
    """
    Compute camera intrinsic parameters.

    Parameters
    ----------
    image_width   : int    Image width in pixels.
    image_height  : int    Image height in pixels.
    fov_h_degrees : float  Horizontal field of view in degrees (CARLA default 90°).

    Returns
    -------
    dict with keys:
        "fx"          : float  Focal length x (pixels)
        "fy"          : float  Focal length y (pixels)
        "cx"          : float  Principal point x (pixels)
        "cy"          : float  Principal point y (pixels)
        "image_width" : int
        "image_height": int
        "fov_h"       : float  Horizontal FOV (degrees)
        "fov_v"       : float  Vertical FOV (degrees, derived)
        "K"           : list   3×3 matrix as nested list (row-major)
    """
    fov_h_rad = math.radians(fov_h_degrees)

    # Focal length from horizontal FOV
    fx = image_width / (2.0 * math.tan(fov_h_rad / 2.0))

    # Assume square pixels → fy = fx
    fy = fx

    # Principal point at image centre
    cx = image_width  / 2.0
    cy = image_height / 2.0

    # Derive vertical FOV
    fov_v_rad = 2.0 * math.atan(image_height / (2.0 * fy))
    fov_v_degrees = math.degrees(fov_v_rad)

    K = [
        [fx,  0.0, cx],
        [0.0, fy,  cy],
        [0.0, 0.0, 1.0],
    ]

    return {
        "fx":           fx,
        "fy":           fy,
        "cx":           cx,
        "cy":           cy,
        "image_width":  image_width,
        "image_height": image_height,
        "fov_h":        fov_h_degrees,
        "fov_v":        fov_v_degrees,
        "K":            K,
    }
