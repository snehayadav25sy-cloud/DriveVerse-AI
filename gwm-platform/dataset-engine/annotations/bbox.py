"""
annotations/bbox.py — distance + camera FOV filtering and 2-D bbox projection.

SCOPE DECISION (intentional, do not "fix" without a build review):
  This module implements EXACTLY TWO filters, applied in order:
    1. Distance filter  — drops actors beyond max_range metres
    2. Camera FOV filter — drops actors outside the camera's view frustum
                           (pure angle/geometry, no line-of-sight checks)

  Line-of-sight analysis and vis-scoring are explicitly
  OUT OF SCOPE for Build 2. An actor that is geometrically within the FOV
  but physically behind a wall will still be labeled. This is a known,
  accepted limitation deferred to a future Dataset Quality Engine build
  (Build 4+). Do not add line-of-sight checks here without a separate design review.

All inputs are plain Python dicts/floats — no CARLA types allowed.
"""

import math
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def filter_and_project(
    actor: dict,
    ego_transform: dict,
    camera_params: dict,
    max_range: float = 100.0,
) -> Optional[dict]:
    """
    Apply distance + FOV filters, then project the actor's 3-D bounding box
    centre into 2-D image coordinates.

    Parameters
    ----------
    actor : dict
        Keys required:
          "location"    : {"x": float, "y": float, "z": float}  (world coords)
          "extent"      : {"x": float, "y": float, "z": float}  (half-extents)
          "internal_class" : str  (already mapped by class_mapping.py)
          "track_id"    : int
          "velocity"    : {"x": float, "y": float, "z": float}
          "blueprint_id": str
    ego_transform : dict
        Keys: "x", "y", "z", "yaw" (degrees)  — ego vehicle world pose
    camera_params : dict
        Keys:
          "fov_h"       : float  horizontal FOV in degrees
          "fov_v"       : float  vertical FOV in degrees
          "image_width" : int
          "image_height": int
          "fx"          : float  (focal length x, pixels)
          "fy"          : float  (focal length y, pixels)
          "cx"          : float  (principal point x)
          "cy"          : float  (principal point y)
    max_range : float
        Distance threshold in metres (default 100 m, matches LiDAR range).

    Returns
    -------
    dict | None
        None if the actor is filtered out.
        Otherwise a dict with:
          "internal_class", "track_id", "blueprint_id",
          "bbox2d"   : (x_min, y_min, x_max, y_max) in pixel coords
          "position3d": (x, y, z) in ego-relative coords (metres)
          "velocity" : (vx, vy, vz) in m/s
          "distance" : float  metres from ego
    """
    loc = actor["location"]
    ego = ego_transform

    # ── 1. Distance filter ──────────────────────────────────────────────────
    dx = loc["x"] - ego["x"]
    dy = loc["y"] - ego["y"]
    dz = loc["z"] - ego["z"]
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)

    if distance > max_range:
        return None  # too far

    # ── 2. Camera FOV filter ─────────────────────────────────────────────────
    # Transform actor position into ego-relative forward/right/up frame.
    yaw_rad = math.radians(ego.get("yaw", 0.0))
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)

    # Forward component (camera optical axis is along vehicle forward)
    fwd   =  cos_yaw * dx + sin_yaw * dy
    right = -sin_yaw * dx + cos_yaw * dy
    up    = dz

    # Actor must be in FRONT of the camera
    if fwd <= 0.0:
        return None  # behind ego

    # Horizontal angle from forward axis
    h_angle_deg = math.degrees(math.atan2(right, fwd))
    v_angle_deg = math.degrees(math.atan2(up, fwd))

    half_fov_h = camera_params["fov_h"] / 2.0
    half_fov_v = camera_params["fov_v"] / 2.0

    if abs(h_angle_deg) > half_fov_h:
        return None  # outside horizontal FOV
    if abs(v_angle_deg) > half_fov_v:
        return None  # outside vertical FOV

    # ── 3. 2-D bounding box projection ──────────────────────────────────────
    # Project the actor's bounding box corners into image space using the
    # pinhole camera model with the intrinsic parameters.
    ext = actor.get("extent", {"x": 1.0, "y": 0.5, "z": 0.75})
    bbox2d = _project_bbox(
        fwd, right, up, ext, camera_params
    )

    vel = actor.get("velocity", {"x": 0.0, "y": 0.0, "z": 0.0})

    return {
        "internal_class": actor["internal_class"],
        "track_id":       actor["track_id"],
        "blueprint_id":   actor.get("blueprint_id", ""),
        "bbox2d":         bbox2d,
        "position3d":     (fwd, right, up),
        "velocity":       (vel["x"], vel["y"], vel["z"]),
        "distance":       distance,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _project_bbox(
    fwd: float, right: float, up: float,
    extent: dict,
    cam: dict,
) -> Tuple[int, int, int, int]:
    """
    Project 8 corners of the 3-D bounding box (axis-aligned in ego frame)
    to 2-D image coordinates, return the enclosing 2-D rectangle.

    Uses pinhole model:  u = fx * (right/fwd) + cx
                         v = fy * (-up/fwd)   + cy

    (CARLA camera: x=right, y=down, z=forward — we adapt here.)
    """
    ex, ey, ez = extent["x"], extent["y"], extent["z"]
    fx = cam["fx"]
    fy = cam["fy"]
    cx = cam["cx"]
    cy = cam["cy"]
    W  = cam["image_width"]
    H  = cam["image_height"]

    u_vals, v_vals = [], []

    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                # Corner in ego-relative frame
                c_fwd   = fwd   + sx * ex
                c_right = right + sy * ey
                c_up    = up    + sz * ez

                if c_fwd <= 0.01:
                    continue  # corner behind camera plane

                u = fx * (c_right / c_fwd) + cx
                v = fy * (-c_up   / c_fwd) + cy
                u_vals.append(u)
                v_vals.append(v)

    if not u_vals:
        # Degenerate — use centre projection
        u_c = int(fx * (right / fwd) + cx)
        v_c = int(fy * (-up   / fwd) + cy)
        return (u_c - 10, v_c - 10, u_c + 10, v_c + 10)

    x_min = max(0, int(min(u_vals)))
    y_min = max(0, int(min(v_vals)))
    x_max = min(W, int(max(u_vals)))
    y_max = min(H, int(max(v_vals)))

    return (x_min, y_min, x_max, y_max)
