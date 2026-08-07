"""
Phase 8 tests — Dataset validation
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import tempfile
from app.scenario_execution.validation.execution_validator import DatasetValidator

PASS, FAIL = "PASS", "FAIL"
results = []

def check(condition, description):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")

def test_8_1_complete_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "rgb"))
        os.makedirs(os.path.join(tmpdir, "provenance"))
        for i in range(5):
            with open(os.path.join(tmpdir, "rgb", f"{i:06d}.png"), "wb") as f:
                f.write(b"PNGDATA" * 100)
        with open(os.path.join(tmpdir, "manifest.json"), "w") as f:
            f.write("{}")
        with open(os.path.join(tmpdir, "provenance", "execution_provenance.json"), "w") as f:
            f.write("{}")
        validator = DatasetValidator(tmpdir, expected_frames=5)
        report = validator.validate()
        check(report.passed is True, "Complete dataset passes validation")
        check(report.actual_frames == 5, "Actual frames correct")

def test_8_2_missing_frames():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "rgb"))
        for i in range(3):
            with open(os.path.join(tmpdir, "rgb", f"{i:06d}.png"), "w") as f:
                f.write("data")
        with open(os.path.join(tmpdir, "manifest.json"), "w") as f:
            f.write("{}")
        validator = DatasetValidator(tmpdir, expected_frames=5)
        report = validator.validate()
        check(report.passed is False, "Missing frames fails validation")
        check(len(report.missing_frames) == 2, "Two missing frames")

if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 8 - Validation Tests")
    print("=" * 65)
    try:
        test_8_1_complete_dataset()
        test_8_2_missing_frames()
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
