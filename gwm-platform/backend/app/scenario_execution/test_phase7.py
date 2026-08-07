"""
Phase 7 tests — Recording engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import tempfile
import json
from app.scenario_execution.recording.recorder import RecordingEngine

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_7_1_recording():
    with tempfile.TemporaryDirectory() as tmpdir:
        recorder = RecordingEngine(tmpdir, "session_001")
        recorder.initialize(["rgb", "lidar"])
        recorder.record_frame(0, {"rgb": "rgb_000000.png", "lidar": "lidar_000000.pcd"})
        recorder.record_frame(1, {"rgb": "rgb_000001.png", "lidar": "lidar_000001.pcd"})
        manifest = recorder.finalize()
        check(manifest.frame_count == 2, "Two frames recorded")
        check(manifest.complete is True, "Manifest complete")
        check(os.path.exists(os.path.join(tmpdir, "manifest.json")), "Manifest written")
        check(os.path.exists(os.path.join(tmpdir, "frame_index.json")), "Frame index written")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 7 - Recording Tests")
    print("=" * 65)
    try:
        test_7_1_recording()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
