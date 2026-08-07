"""
Phase 12 tests — Sensor calibration
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import math
import numpy as np
from app.sensor_realism.calibration import (
    compute_intrinsic_matrix,
    compute_extrinsic_matrix,
    invert_extrinsic,
    compute_camera_to_camera_transform,
)

PASS, FAIL = "PASS", "FAIL"
results = []

def check(c, d):
    s = PASS if c else FAIL
    results.append((s, d))
    print(f"  [{s}]  {d}")
    if not c: raise AssertionError(f"CHECK FAILED: {d}")

def test_12_1_intrinsic_matrix():
    K = compute_intrinsic_matrix(1280, 720, 90.0)
    check(len(K) == 3 and len(K[0]) == 3, "K is 3x3")
    check(K[0][2] == 640.0, "Principal point x")
    check(K[1][2] == 360.0, "Principal point y")
    check(K[0][0] > 0, "fx > 0")
    check(K[1][1] > 0, "fy > 0")

def test_12_2_extrinsic_matrix():
    E = compute_extrinsic_matrix((1.5, 0.0, 1.4), (0.0, 0.0, 0.0))
    check(len(E) == 4 and len(E[0]) == 4, "E is 4x4")
    check(E[0][3] == 1.5, "Translation x")
    check(E[1][3] == 0.0, "Translation y")

def test_12_3_invert_extrinsic():
    E = compute_extrinsic_matrix((1.5, 0.0, 1.4), (0.0, 0.0, 0.0))
    E_inv = invert_extrinsic(E)
    check(len(E_inv) == 4, "Inverse is 4x4")
    identity = np.array(E) @ np.array(E_inv)
    check(np.allclose(identity, np.eye(4), atol=1e-6), "E @ E_inv = I")

def test_12_4_camera_to_camera():
    E1 = compute_extrinsic_matrix((1.5, 0.0, 1.4), (0.0, 0.0, 0.0))
    E2 = compute_extrinsic_matrix((0.0, -0.5, 1.4), (0.0, -90.0, 0.0))
    rel = compute_camera_to_camera_transform(E1, E2)
    check(len(rel) == 4, "Relative transform is 4x4")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 12 - Sensor Calibration Tests")
    print("=" * 65)
    try:
        test_12_1_intrinsic_matrix()
        test_12_2_extrinsic_matrix()
        test_12_3_invert_extrinsic()
        test_12_4_camera_to_camera()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0: sys.exit(1)

