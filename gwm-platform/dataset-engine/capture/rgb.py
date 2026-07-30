"""
capture/rgb.py — RGB capture output handler.

Receives already-captured image bytes (or a file path) and frame_id,
writes images/{frame:06d}.png into the dataset output directory.

Design: no CARLA imports. The caller (worker/simulator/carla/capture.py)
converts the CARLA image to bytes before passing it here.
"""

import os
import shutil


def save_rgb(image_bytes: bytes, frame_id: int, output_dir: str) -> str:
    """
    Write raw PNG bytes for one frame.

    Parameters
    ----------
    image_bytes : bytes   Raw PNG-encoded image data.
    frame_id    : int     Zero-based frame index (used as filename stem).
    output_dir  : str     Root dataset directory; images/ sub-dir is created.

    Returns
    -------
    str  Absolute path of the written file.
    """
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    path = os.path.join(images_dir, f"{frame_id:06d}.png")
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def save_rgb_from_path(src_path: str, frame_id: int, output_dir: str) -> str:
    """
    Copy an already-written PNG (e.g. saved by CARLA directly) into the
    canonical images/ directory under the dataset root.

    Parameters
    ----------
    src_path   : str  Source PNG path written by CARLA's save_to_disk().
    frame_id   : int  Zero-based frame index.
    output_dir : str  Root dataset directory.

    Returns
    -------
    str  Absolute path of the destination file.
    """
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    dst_path = os.path.join(images_dir, f"{frame_id:06d}.png")
    shutil.copy2(src_path, dst_path)
    return dst_path
