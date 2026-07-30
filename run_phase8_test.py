"""
Phase 8 Calibration & Expanded Export Engine Test.
Validates intrinsics, extrinsics, KITTI, nuScenes, and COCO exporter formats.
"""

import os
import sys
import json

backend_path = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\backend")
sys.path.insert(0, backend_path)
worker_path  = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\worker")
sys.path.insert(0, worker_path)
engine_path  = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\dataset-engine")
sys.path.insert(0, engine_path)

from calibration.intrinsics import compute_intrinsics
from calibration.extrinsics import compute_extrinsics
from exporters.kitti import export_kitti
from exporters.nuscenes.export import export_nuscenes
from exporters.coco.export import export_coco

# 1. Test Calibration Engine
intr = compute_intrinsics(1280, 720, 90.0)
assert "K" in intr and intr["image_width"] == 1280, "Intrinsics validation failed!"
print("1. Calibration Intrinsics: PASSED")

ext = compute_extrinsics()
assert "T_cam_to_lidar" in ext and "T_lidar_to_cam" in ext, "Extrinsics validation failed!"
print("2. Calibration Extrinsics: PASSED")

# 2. Test Exporters on sample directory
sample_dir = os.path.abspath(r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\storage\sample_test_phase8")
os.makedirs(os.path.join(sample_dir, "images"), exist_ok=True)
os.makedirs(os.path.join(sample_dir, "labels"), exist_ok=True)

# Write dummy image and label frame 0
with open(os.path.join(sample_dir, "images", "000000.png"), "wb") as f:
    f.write(b"")

with open(os.path.join(sample_dir, "labels", "000000.txt"), "w") as f:
    f.write("car 0.00 10.00 5.00 0.00 1.50 0.00\n")

# KITTI export
k_path = export_kitti(sample_dir, 1, intr, ext, ["rgb", "lidar"])
assert os.path.exists(k_path), "KITTI export path missing!"
print("3. KITTI Exporter: PASSED")

# nuScenes export
n_path = export_nuscenes(sample_dir, 1, ["rgb", "lidar", "radar"])
assert os.path.exists(os.path.join(n_path, "v1.0-mini", "scene.json")), "nuScenes scene.json missing!"
print("4. nuScenes Exporter: PASSED")

# COCO export
c_path = export_coco(sample_dir, 1)
assert os.path.exists(os.path.join(c_path, "instances_default.json")), "COCO instances_default.json missing!"
print("5. COCO Exporter: PASSED")

print("\nPhase 8 (Calibration & Expanded Export Engine): ALL TESTS PASSED")
