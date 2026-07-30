# -*- coding: utf-8 -*-
"""
tests/test_phase1.py - Phase 1 standalone validation.

Runs entirely without CARLA (pure Python, no server needed).
Generates synthetic actor data, runs the full annotation pipeline,
writes internal + KITTI formats, then validates the output.

Usage:
    python dataset-engine/tests/test_phase1.py
"""

import os
import sys
import io
import json
import shutil
import tempfile

# Force UTF-8 stdout on Windows (avoids cp1252 encoding errors)
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure dataset-engine is importable from project root
ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ENGINE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, ENGINE)

from capture.rgb   import save_rgb
from capture.lidar import save_lidar

from annotations.class_mapping import map_blueprint, PEDESTRIAN, CAR, TRUCK, DONTCARE
from annotations.classify       import classify_actors
from annotations.tracking       import ObjectTracker
from annotations.bbox           import filter_and_project

from calibration.intrinsics import compute_intrinsics
from calibration.extrinsics import compute_extrinsics

from metadata.frame_metadata import write_frame_metadata

from exporters.internal            import write_labels, write_calibration, read_labels
from exporters.class_mapping_kitti import to_kitti, INTERNAL_TO_KITTI
from exporters.kitti               import export_kitti


# ---------------------------------------------------------------------------
PASS = "OK"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


# ---------------------------------------------------------------------------
def test_class_mapping():
    print("\n[1] Class mapping correctness")

    check(map_blueprint("vehicle.tesla.model3")          == CAR,        "tesla.model3 -> CAR")
    check(map_blueprint("vehicle.carlamotors.firetruck") == TRUCK,      "firetruck -> TRUCK")
    check(map_blueprint("walker.pedestrian.0001")        == PEDESTRIAN, "pedestrian wildcard -> PEDESTRIAN")
    check(map_blueprint("static.prop.barrel")            == DONTCARE,   "static.prop wildcard -> DONTCARE")
    check(map_blueprint("vehicle.unknown.model")         == CAR,        "unknown vehicle fallback -> CAR")
    check(map_blueprint("completely.unknown.actor")      == DONTCARE,   "totally unknown -> DONTCARE")


def test_kitti_class_mapping():
    print("\n[2] KITTI class mapping isolation")

    check(to_kitti("CAR")        == "Car",        "CAR -> Car")
    check(to_kitti("PEDESTRIAN") == "Pedestrian", "PEDESTRIAN -> Pedestrian")
    check(to_kitti("DONTCARE")   == "DontCare",   "DONTCARE -> DontCare")

    # Verify KITTI strings only appear in class_mapping_kitti, not in bbox/classify
    import inspect
    import annotations.bbox     as bbox_mod
    import annotations.classify as classify_mod

    kitti_strings = {"Car", "Van", "Truck", "Pedestrian", "Cyclist", "Tram", "Misc", "DontCare"}
    for mod, name in [(bbox_mod, "bbox.py"), (classify_mod, "classify.py")]:
        src   = inspect.getsource(mod)
        found = [s for s in kitti_strings if f'"{s}"' in src or f"'{s}'" in src]
        check(len(found) == 0,
              f"{name} contains zero literal KITTI class strings (found: {found})")


def test_intrinsics():
    print("\n[3] Camera intrinsics")

    intr = compute_intrinsics(1280, 720, fov_h_degrees=90.0)
    check(abs(intr["fx"] - 640.0) < 1.0, "fx approx 640 for 1280px 90-deg FOV")
    check(intr["cx"] == 640.0,            "cx = image_width / 2")
    check(intr["cy"] == 360.0,            "cy = image_height / 2")
    check(len(intr["K"]) == 3 and len(intr["K"][0]) == 3, "K is 3x3")
    check(intr["K"][0][0] == intr["fx"],  "K[0][0] = fx")


def test_extrinsics():
    print("\n[4] Sensor extrinsics")

    ext = compute_extrinsics()
    check("T_cam_to_lidar" in ext, "T_cam_to_lidar present")
    check("T_lidar_to_cam" in ext, "T_lidar_to_cam present")
    T = ext["T_cam_to_lidar"]
    check(len(T) == 4 and len(T[0]) == 4,      "T_cam_to_lidar is 4x4")
    check(abs(T[0][3] - (-1.5)) < 1e-6,        "Translation x = -1.5 m (camera ahead of LiDAR)")


def test_bbox_filters():
    print("\n[5] bbox distance + FOV filters")

    import inspect
    import annotations.bbox as bbox_mod
    src = inspect.getsource(bbox_mod)
    for kw in ["ray_cast", "raycast", "visibility", "occlusion"]:
        check(kw not in src.lower(), f"bbox.py has no '{kw}' code")

    cam = compute_intrinsics(1280, 720, 90.0)
    ego = {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0}

    # Actor 50 m ahead - should pass
    actor_close = {
        "location":       {"x": 50.0, "y": 0.0, "z": 0.0},
        "extent":         {"x": 2.0,  "y": 1.0, "z": 0.75},
        "internal_class": CAR,
        "track_id":       1,
        "velocity":       {"x": 0.0, "y": 0.0, "z": 0.0},
        "blueprint_id":   "vehicle.tesla.model3",
        "actor_id":       100,
    }
    result_close = filter_and_project(actor_close, ego, cam, max_range=100.0)
    check(result_close is not None,              "Actor 50m ahead passes distance+FOV filter")
    check("bbox2d" in result_close,              "Result has bbox2d")
    check(len(result_close["bbox2d"]) == 4,      "bbox2d has 4 coords")

    # Actor 150 m away - should be filtered by distance
    actor_far = dict(actor_close)
    actor_far["location"] = {"x": 150.0, "y": 0.0, "z": 0.0}
    result_far = filter_and_project(actor_far, ego, cam, max_range=100.0)
    check(result_far is None, "Actor 150m away filtered by distance")

    # Actor 10 m behind ego - should be filtered by FOV
    actor_behind = dict(actor_close)
    actor_behind["location"] = {"x": -10.0, "y": 0.0, "z": 0.0}
    result_behind = filter_and_project(actor_behind, ego, cam, max_range=100.0)
    check(result_behind is None, "Actor behind ego filtered by FOV")


def test_full_pipeline(tmpdir: str):
    print("\n[6] Full pipeline: capture -> annotate -> internal -> KITTI")

    FRAMES  = 5
    sensors = ["rgb", "lidar"]

    tracker    = ObjectTracker()
    intr       = compute_intrinsics(1280, 720, 90.0)
    ext        = compute_extrinsics()
    cam_params = {**intr}
    ego        = {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0}

    # Synthetic actors: car ahead, pedestrian in FOV, prop (DONTCARE), distant car
    raw_actors_template = [
        {"actor_id": 1, "blueprint_id": "vehicle.tesla.model3",
         "location": {"x": 30.0, "y": 0.0, "z": 0.5},
         "extent":   {"x": 2.0,  "y": 1.0, "z": 0.75},
         "velocity": {"x": -5.0, "y": 0.0, "z": 0.0}},
        {"actor_id": 2, "blueprint_id": "walker.pedestrian.0001",
         "location": {"x": 20.0, "y": 3.0, "z": 0.9},
         "extent":   {"x": 0.4,  "y": 0.4, "z": 0.9},
         "velocity": {"x": 0.0,  "y": 1.0, "z": 0.0}},
        {"actor_id": 3, "blueprint_id": "static.prop.barrel",
         "location": {"x": 15.0, "y": 1.0, "z": 0.4},
         "extent":   {"x": 0.3,  "y": 0.3, "z": 0.5},
         "velocity": {"x": 0.0,  "y": 0.0, "z": 0.0}},
        {"actor_id": 4, "blueprint_id": "vehicle.audi.etron",
         "location": {"x": 200.0, "y": 0.0, "z": 0.5},   # too far
         "extent":   {"x": 2.0,   "y": 1.0, "z": 0.75},
         "velocity": {"x": 0.0,   "y": 0.0, "z": 0.0}},
    ]

    import math
    for frame_id in range(FRAMES):
        tick = 1000 + frame_id

        # Minimal valid 1x1 PNG
        png_bytes = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00"
            b"\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00"
            b"\x05\xfe\x02\xfe\xdc\xccY\xe7"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        save_rgb(png_bytes, frame_id, tmpdir)

        # 20 synthetic LiDAR points
        points = []
        for p in range(20):
            angle = (p / 20) * 2 * math.pi
            points.append((math.cos(angle) * 10, math.sin(angle) * 10, p * 0.2, 0.8))
        save_lidar(points, frame_id, tmpdir)

        # Annotation pipeline
        classified = classify_actors(raw_actors_template)
        tracked    = tracker.assign(classified)
        annotated  = []
        for actor in tracked:
            result = filter_and_project(actor, ego, cam_params, max_range=100.0)
            if result is not None:
                annotated.append(result)

        write_labels(frame_id, annotated, tmpdir)
        write_frame_metadata(
            frame_id, tick, tmpdir,
            town="Town01",
            sensors_present=sensors,
            speed_ms=10.0 + frame_id,
            sim_elapsed_seconds=frame_id * 0.1,
        )

    # Calibration once
    write_calibration(tmpdir, intr, ext)

    # --- Validate internal format ---
    for frame_id in range(FRAMES):
        stem = f"{frame_id:06d}"
        check(os.path.exists(os.path.join(tmpdir, "images",     f"{stem}.png")),  f"images/{stem}.png exists")
        check(os.path.exists(os.path.join(tmpdir, "pointcloud", f"{stem}.pcd")),  f"pointcloud/{stem}.pcd exists")
        check(os.path.exists(os.path.join(tmpdir, "labels",     f"{stem}.txt")),  f"labels/{stem}.txt exists")
        check(os.path.exists(os.path.join(tmpdir, "metadata",   f"{stem}.json")), f"metadata/{stem}.json exists")

    check(os.path.exists(os.path.join(tmpdir, "calibration", "calib.json")),
          "calibration/calib.json exists")

    actors_f0  = read_labels(0, tmpdir)
    classes_f0 = [a["internal_class"] for a in actors_f0]
    check("CAR"        in classes_f0, "Frame 0 labels contain CAR")
    check("PEDESTRIAN" in classes_f0, "Frame 0 labels contain PEDESTRIAN")

    actors_f1 = read_labels(1, tmpdir)
    if actors_f0 and actors_f1:
        ids_f0 = {a["track_id"] for a in actors_f0}
        ids_f1 = {a["track_id"] for a in actors_f1}
        check(ids_f0 == ids_f1, "Track IDs stable across frames 0 and 1")

    with open(os.path.join(tmpdir, "calibration", "calib.json")) as f:
        calib = json.load(f)
    check("camera_intrinsics" in calib, "calib.json has camera_intrinsics")
    check("sensor_extrinsics" in calib, "calib.json has sensor_extrinsics")
    check("K"                 in calib["camera_intrinsics"], "camera_intrinsics has K matrix")
    check("T_cam_to_lidar"    in calib["sensor_extrinsics"], "extrinsics has T_cam_to_lidar")

    # --- KITTI export ---
    export_kitti(tmpdir, FRAMES, intr, ext, sensors)

    kitti_dir = os.path.join(tmpdir, "kitti")
    for frame_id in range(FRAMES):
        stem = f"{frame_id:06d}"
        check(os.path.exists(os.path.join(kitti_dir, "image_2",  f"{stem}.png")), f"kitti/image_2/{stem}.png exists")
        check(os.path.exists(os.path.join(kitti_dir, "velodyne", f"{stem}.bin")), f"kitti/velodyne/{stem}.bin exists")
        check(os.path.exists(os.path.join(kitti_dir, "label_2",  f"{stem}.txt")), f"kitti/label_2/{stem}.txt exists")
        check(os.path.exists(os.path.join(kitti_dir, "calib",    f"{stem}.txt")), f"kitti/calib/{stem}.txt exists")

    with open(os.path.join(kitti_dir, "label_2", "000000.txt")) as f:
        kitti_lines = f.read()
    check("Car"        in kitti_lines, "KITTI label_2/000000.txt contains 'Car'")
    check("Pedestrian" in kitti_lines, "KITTI label_2/000000.txt contains 'Pedestrian'")

    with open(os.path.join(kitti_dir, "calib", "000000.txt")) as f:
        calib_txt = f.read()
    check("P2:"             in calib_txt, "KITTI calib has P2 matrix")
    check("Tr_velo_to_cam:" in calib_txt, "KITTI calib has Tr_velo_to_cam")

    velo_size = os.path.getsize(os.path.join(kitti_dir, "velodyne", "000000.bin"))
    check(velo_size > 0, f"kitti/velodyne/000000.bin non-empty ({velo_size} bytes)")


def test_no_carla_import():
    print("\n[7] Grep check: zero real 'import carla' in dataset-engine/ (excl. tests/)")

    engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tests_dir  = os.path.abspath(os.path.dirname(__file__))
    violations = []
    for dirpath, dirnames, filenames in os.walk(engine_dir):
        # Skip the tests/ directory — test file contains the search string in literals
        dirnames[:] = [d for d in dirnames
                       if os.path.abspath(os.path.join(dirpath, d)) != tests_dir]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    stripped = line.strip()
                    # Only flag actual import statements, not string literals
                    if stripped.startswith("import carla") or stripped.startswith("from carla"):
                        violations.append(f"{fpath}:{i}: {stripped}")

    check(len(violations) == 0,
          f"Zero real carla imports in dataset-engine/ (found: {violations})")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 1 - dataset-engine standalone validation")
    print("=" * 65)

    tmpdir = tempfile.mkdtemp(prefix="gwm_phase1_")
    print(f"\n  Output dir: {tmpdir}")

    try:
        test_class_mapping()
        test_kitti_class_mapping()
        test_intrinsics()
        test_extrinsics()
        test_bbox_filters()
        test_full_pipeline(tmpdir)
        test_no_carla_import()
    except AssertionError:
        pass  # error already printed
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 65)
    passed = sum(1 for s, _ in results if s == PASS)
    failed = sum(1 for s, _ in results if s == FAIL)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)
