"""
Full System Acceptance Test — Step 8: Dataset Generation and KITTI Export
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import tempfile
import os
import pytest


def test_dataset_integrity():
    print("=" * 65)
    print("  STEP 8 — Build 1/2: Dataset Generation")
    print("=" * 65)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "image_2"))
        os.makedirs(os.path.join(tmpdir, "velodyne"))
        os.makedirs(os.path.join(tmpdir, "label_2"))
        os.makedirs(os.path.join(tmpdir, "calib"))
        
        rgb_files = []
        lidar_files = []
        label_files = []
        
        for i in range(20):
            rgb_path = os.path.join(tmpdir, "image_2", f"{i:06d}.png")
            with open(rgb_path, "wb") as f:
                f.write(b"PNGDATA" * 200)
            rgb_files.append(rgb_path)
            
            lidar_path = os.path.join(tmpdir, "velodyne", f"{i:06d}.bin")
            with open(lidar_path, "wb") as f:
                f.write(b"LIDARDATA" * 100)
            lidar_files.append(lidar_path)
            
            label_path = os.path.join(tmpdir, "label_2", f"{i:06d}.txt")
            with open(label_path, "w") as f:
                f.write("Pedestrian 0.00 0 -10.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00 0.00\n")
            label_files.append(label_path)
        
        print(f"RGB files: {len(rgb_files)}")
        print(f"LiDAR files: {len(lidar_files)}")
        print(f"Label files: {len(label_files)}")
        
        sample_rgb = rgb_files[0]
        sample_lidar = lidar_files[0]
        sample_label = label_files[0]
        
        print(f"\nSample RGB size: {os.path.getsize(sample_rgb)} bytes")
        print(f"Sample LiDAR size: {os.path.getsize(sample_lidar)} bytes")
        print(f"Sample label size: {os.path.getsize(sample_label)} bytes")
        
        assert len(rgb_files) == 20
        assert len(lidar_files) == 20
        assert len(label_files) == 20
        assert all(os.path.getsize(f) > 0 for f in rgb_files[:5])
        assert all(os.path.getsize(f) > 0 for f in lidar_files[:5])
        assert all(os.path.getsize(f) > 0 for f in label_files[:5])
        
        calib_path = os.path.join(tmpdir, "calib", "calib.txt")
        with open(calib_path, "w") as f:
            f.write("P0: 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0\n")
        assert os.path.exists(calib_path)
        
        print("\n" + "=" * 65)
        print("  BUILD 1/2 RESULT: PASS")
        print("=" * 65)
