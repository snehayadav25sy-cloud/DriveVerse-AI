"""
prompt-engine/schemas/test_scenario_schema.py
=============================================
Phase 1 unit tests for the Scenario JSON schema.
Run with: python test_scenario_schema.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout.reconfigure(line_buffering=True)

from schemas.scenario_schema import ScenarioConfig, WeatherConfig, TrafficConfig
from pydantic import ValidationError

PASS = 0
FAIL = 0

def expect_valid(label: str, **kwargs):
    global PASS, FAIL
    try:
        cfg = ScenarioConfig(**kwargs)
        print(f"  [PASS] VALID — {label}", flush=True)
        PASS += 1
        return cfg
    except Exception as e:
        print(f"  [FAIL] VALID — {label}: should have passed but got: {e}", flush=True)
        FAIL += 1
        return None

def expect_invalid(label: str, **kwargs):
    global PASS, FAIL
    try:
        ScenarioConfig(**kwargs)
        print(f"  [FAIL] INVALID — {label}: should have been rejected but passed!", flush=True)
        FAIL += 1
    except (ValidationError, ValueError) as e:
        first_err = str(e).split("\n")[0]
        print(f"  [PASS] INVALID — {label}: correctly rejected → {first_err}", flush=True)
        PASS += 1

print("=" * 65)
print("Phase 1 — Scenario JSON Schema Tests")
print("=" * 65)

# ── Valid scenarios ────────────────────────────────────────────────────────────
print("\n[Valid cases]")
expect_valid(
    "Basic urban RGB job",
    map="Town01", sensors=["rgb"], frames=500, export_format="kitti",
)
expect_valid(
    "Highway multi-sensor KITTI",
    map="Town03", sensors=["rgb", "lidar", "radar"], frames=1000,
    export_format="kitti",
    road="highway",
    weather=WeatherConfig(rain=0.8, fog=0.1, cloudiness=0.7),
    traffic=TrafficConfig(cars=80, trucks=20),
    pedestrians=0,
)
expect_valid(
    "Suburban RGB+depth COCO",
    map="Town02", sensors=["rgb", "depth"], frames=250, export_format="coco",
    road="residential",
)
expect_valid(
    "Minimal frames edge (1 frame)",
    map="Town01", sensors=["rgb"], frames=1, export_format="kitti",
)
expect_valid(
    "Max frames edge (2000 frames)",
    map="Town01", sensors=["rgb"], frames=2000, export_format="kitti",
)
expect_valid(
    "All 7 sensors at once",
    map="Town01",
    sensors=["rgb", "lidar", "radar", "depth", "semantic", "instance", "optical_flow"],
    frames=100, export_format="kitti",
)

# ── Invalid cases (must be rejected with clear error) ─────────────────────────
print("\n[Invalid cases — all must be REJECTED]")
expect_invalid(
    "Unsupported map: Town99",
    map="Town99", sensors=["rgb"], frames=100, export_format="kitti",
)
expect_invalid(
    "Negative frame count: -1",
    map="Town01", sensors=["rgb"], frames=-1, export_format="kitti",
)
expect_invalid(
    "Unsupported sensor: sonar",
    map="Town01", sensors=["rgb", "sonar"], frames=100, export_format="kitti",
)
expect_invalid(
    "Unsupported export format: yolo",
    map="Town01", sensors=["rgb"], frames=100, export_format="yolo",
)
expect_invalid(
    "Empty sensor list",
    map="Town01", sensors=[], frames=100, export_format="kitti",
)
expect_invalid(
    "Frames exceed max (2001)",
    map="Town01", sensors=["rgb"], frames=2001, export_format="kitti",
)
expect_invalid(
    "Unsupported road type: airstrip",
    map="Town01", sensors=["rgb"], frames=100, export_format="kitti",
    road="airstrip",
)
expect_invalid(
    "Unknown map: London (not a CARLA map)",
    map="London", sensors=["rgb"], frames=100, export_format="kitti",
)

# ── to_job_params() bridge test ───────────────────────────────────────────────
print("\n[to_job_params() bridge]")
cfg = ScenarioConfig(map="Town03", sensors=["rgb", "lidar"], frames=500, export_format="kitti")
params = cfg.to_job_params()
assert params == {"map": "Town03", "sensors": ["rgb", "lidar"], "frames": 500, "export_format": "kitti"}, \
    f"to_job_params mismatch: {params}"
print(f"  [PASS] to_job_params() → {params}", flush=True)
PASS += 1

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'=' * 65}")
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
print("ALL TESTS PASSED" if FAIL == 0 else f"{FAIL} TESTS FAILED")
print("=" * 65)
sys.exit(0 if FAIL == 0 else 1)
