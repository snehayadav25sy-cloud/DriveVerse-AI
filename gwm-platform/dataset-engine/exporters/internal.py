"""
exporters/internal.py — canonical internal format writer.

This exporter ALWAYS runs first and is the source of truth.
No other exporter generates data directly from raw CARLA output —
they all read what internal.py wrote.

Internal label file format (labels/{frame:06d}.txt):
  One line per actor, space-separated:
    internal_class track_id x_min y_min x_max y_max pos_fwd pos_right pos_up vx vy vz distance blueprint_id

Calibration file (calibration/calib.json): written once per dataset.
"""

import os
import json


def write_labels(
    frame_id: int,
    annotated_actors: list,
    output_dir: str,
) -> str:
    """
    Write internal-format label file for one frame.

    Parameters
    ----------
    frame_id          : int   Zero-based frame index.
    annotated_actors  : list  Output of bbox.filter_and_project() — dicts with
                              "internal_class", "track_id", "bbox2d",
                              "position3d", "velocity", "distance", "blueprint_id".
    output_dir        : str   Root dataset directory.

    Returns
    -------
    str  Path of the written label file.
    """
    labels_dir = os.path.join(output_dir, "labels")
    os.makedirs(labels_dir, exist_ok=True)
    path = os.path.join(labels_dir, f"{frame_id:06d}.txt")

    with open(path, "w") as f:
        for actor in annotated_actors:
            bbox = actor["bbox2d"]          # (x_min, y_min, x_max, y_max)
            pos  = actor["position3d"]      # (fwd, right, up) ego-relative
            vel  = actor["velocity"]        # (vx, vy, vz)
            line = (
                f"{actor['internal_class']} "
                f"{actor['track_id']} "
                f"{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]} "
                f"{pos[0]:.3f} {pos[1]:.3f} {pos[2]:.3f} "
                f"{vel[0]:.3f} {vel[1]:.3f} {vel[2]:.3f} "
                f"{actor['distance']:.3f} "
                f"{actor.get('blueprint_id', '')}"
            )
            f.write(line + "\n")

    return path


def write_calibration(
    output_dir: str,
    intrinsics: dict,
    extrinsics: dict,
) -> str:
    """
    Write calibration/calib.json — one file per dataset (not per frame).

    Parameters
    ----------
    output_dir  : str   Root dataset directory.
    intrinsics  : dict  Output of calibration/intrinsics.compute_intrinsics().
    extrinsics  : dict  Output of calibration/extrinsics.compute_extrinsics().

    Returns
    -------
    str  Path of the written calibration file.
    """
    calib_dir = os.path.join(output_dir, "calibration")
    os.makedirs(calib_dir, exist_ok=True)
    path = os.path.join(calib_dir, "calib.json")

    payload = {
        "camera_intrinsics": intrinsics,
        "sensor_extrinsics": extrinsics,
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

    return path


def read_labels(frame_id: int, output_dir: str) -> list:
    """
    Parse a label file back into a list of dicts (for KITTI exporter).

    Returns
    -------
    list of dict with keys matching the internal format.
    """
    path = os.path.join(output_dir, "labels", f"{frame_id:06d}.txt")
    actors = []
    if not os.path.exists(path):
        return actors

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # internal_class track_id x_min y_min x_max y_max fwd right up vx vy vz dist bp
            if len(parts) < 13:
                continue
            actors.append({
                "internal_class": parts[0],
                "track_id":       int(parts[1]),
                "bbox2d":         (int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])),
                "position3d":     (float(parts[6]), float(parts[7]), float(parts[8])),
                "velocity":       (float(parts[9]), float(parts[10]), float(parts[11])),
                "distance":       float(parts[12]),
                "blueprint_id":   parts[13] if len(parts) > 13 else "",
            })
    return actors
