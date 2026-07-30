"""
exporters/kitti.py — converts internal format → KITTI dataset layout.

Reads the internal format files (images/, pointcloud/, labels/, calibration/)
and writes a KITTI-compliant directory structure:

  kitti/
    image_2/       000001.png  ...
    velodyne/      000001.bin  ...   (binary float32 x,y,z,intensity)
    label_2/       000001.txt  ...   (KITTI label format)
    calib/         000001.txt  ...   (KITTI calibration format per frame)

KITTI label line format:
  type truncated occluded alpha x1 y1 x2 y2 h w l x y z ry

  For Build 2 (distance+FOV only), unobservable fields are set to defaults:
    truncated = 0.0, occluded = 0, alpha = -1.0
    h, w, l   = 0.0 (3-D box dimensions not yet estimated)
    ry        = 0.0 (heading angle not yet estimated)

KITTI calib format per frame (required fields):
  P0, P1, P2, P3 (3×4 projection matrices)
  R0_rect        (3×3 rectification)
  Tr_velo_to_cam (3×4 LiDAR→camera transform)

Design: this module only calls to_kitti() from class_mapping_kitti.py
for class name conversion — no hard-coded KITTI strings elsewhere.
"""

import os
import struct
import shutil

from exporters.class_mapping_kitti import to_kitti
from exporters.internal import read_labels


def export_kitti(
    output_dir: str,
    frame_count: int,
    intrinsics: dict,
    extrinsics: dict,
    sensors: list,
) -> str:
    """
    Generate KITTI-format export from the internal dataset folder.

    Parameters
    ----------
    output_dir  : str   Root internal dataset directory.
    frame_count : int   Number of frames.
    intrinsics  : dict  Camera intrinsics (from calibration/intrinsics.py).
    extrinsics  : dict  Sensor extrinsics (from calibration/extrinsics.py).
    sensors     : list  e.g. ["rgb", "lidar"]

    Returns
    -------
    str  Path to the kitti/ subdirectory.
    """
    kitti_dir = os.path.join(output_dir, "kitti")
    img2_dir  = os.path.join(kitti_dir, "image_2")
    velo_dir  = os.path.join(kitti_dir, "velodyne")
    lbl2_dir  = os.path.join(kitti_dir, "label_2")
    cal_dir   = os.path.join(kitti_dir, "calib")

    for d in (img2_dir, velo_dir, lbl2_dir, cal_dir):
        os.makedirs(d, exist_ok=True)

    # Pre-compute KITTI calibration matrices
    kitti_calib_str = _build_kitti_calib(intrinsics, extrinsics)

    for frame_id in range(frame_count):
        stem = f"{frame_id:06d}"

        # ── image_2/ ───────────────────────────────────────────────────────
        if "rgb" in sensors:
            src_img = os.path.join(output_dir, "images", f"{stem}.png")
            dst_img = os.path.join(img2_dir, f"{stem}.png")
            if os.path.exists(src_img):
                shutil.copy2(src_img, dst_img)

        # ── velodyne/ — convert ASCII PCD → KITTI binary float32 ──────────
        if "lidar" in sensors:
            src_pcd = os.path.join(output_dir, "pointcloud", f"{stem}.pcd")
            dst_bin = os.path.join(velo_dir, f"{stem}.bin")
            if os.path.exists(src_pcd):
                _pcd_to_kitti_bin(src_pcd, dst_bin)

        # ── label_2/ ──────────────────────────────────────────────────────
        actors = read_labels(frame_id, output_dir)
        _write_kitti_label(actors, lbl2_dir, frame_id)

        # ── calib/ ────────────────────────────────────────────────────────
        cal_path = os.path.join(cal_dir, f"{stem}.txt")
        with open(cal_path, "w") as f:
            f.write(kitti_calib_str)

    print(f"[KITTI Exporter] Export complete -> {kitti_dir} ({frame_count} frames)")
    return kitti_dir


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_kitti_label(actors: list, label_dir: str, frame_id: int):
    """Write one KITTI label_2 file for a frame."""
    path = os.path.join(label_dir, f"{frame_id:06d}.txt")
    with open(path, "w") as f:
        for actor in actors:
            klass = to_kitti(actor["internal_class"])
            bbox  = actor["bbox2d"]     # (x_min, y_min, x_max, y_max)
            pos   = actor["position3d"] # (fwd, right, up)

            # KITTI label: type trunc occ alpha x1 y1 x2 y2 h w l x y z ry
            # Build 2 defaults for unestimated fields (see module docstring)
            line = (
                f"{klass} "
                f"0.0 0 -1.0 "           # truncated occluded alpha
                f"{bbox[0]:.1f} {bbox[1]:.1f} {bbox[2]:.1f} {bbox[3]:.1f} "
                f"0.0 0.0 0.0 "          # h w l (not estimated)
                f"{pos[1]:.3f} {pos[2]:.3f} {pos[0]:.3f} "  # x y z (KITTI convention)
                f"0.0"                   # ry (not estimated)
            )
            f.write(line + "\n")


def _pcd_to_kitti_bin(src_pcd: str, dst_bin: str):
    """Convert ASCII PCD to KITTI velodyne binary (N×4 float32: x,y,z,intensity)."""
    points = []
    in_data = False
    with open(src_pcd) as f:
        for line in f:
            line = line.strip()
            if line == "DATA ascii":
                in_data = True
                continue
            if in_data and line:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        points.append(tuple(float(p) for p in parts[:4]))
                    except ValueError:
                        continue

    with open(dst_bin, "wb") as f:
        for x, y, z, intensity in points:
            f.write(struct.pack("ffff", x, y, z, intensity))


def _build_kitti_calib(intrinsics: dict, extrinsics: dict) -> str:
    """
    Build KITTI calibration text (same string written per frame).

    KITTI requires P0..P3 (3×4), R0_rect (3×3), Tr_velo_to_cam (3×4).
    P2 is the RGB camera projection matrix; P0,P1,P3 are set to P2
    (we only have one camera).
    """
    fx = intrinsics["fx"]
    fy = intrinsics["fy"]
    cx = intrinsics["cx"]
    cy = intrinsics["cy"]

    # 3×4 projection matrix (no baseline offset — monocular)
    P = f"{fx:.6f} 0.000000 {cx:.6f} 0.000000 " \
        f"0.000000 {fy:.6f} {cy:.6f} 0.000000 " \
        f"0.000000 0.000000 1.000000 0.000000"

    # Rectification = identity
    R0 = "1.000000 0.000000 0.000000 " \
         "0.000000 1.000000 0.000000 " \
         "0.000000 0.000000 1.000000"

    # LiDAR → camera transform (first 3 rows of 4×4)
    T = extrinsics["T_lidar_to_cam"]
    Tr = (
        f"{T[0][0]:.6f} {T[0][1]:.6f} {T[0][2]:.6f} {T[0][3]:.6f} "
        f"{T[1][0]:.6f} {T[1][1]:.6f} {T[1][2]:.6f} {T[1][3]:.6f} "
        f"{T[2][0]:.6f} {T[2][1]:.6f} {T[2][2]:.6f} {T[2][3]:.6f}"
    )

    return (
        f"P0: {P}\n"
        f"P1: {P}\n"
        f"P2: {P}\n"
        f"P3: {P}\n"
        f"R0_rect: {R0}\n"
        f"Tr_velo_to_cam: {Tr}\n"
    )
