"""
scenario_estimator.py — Build 3.4: Scenario Resource Estimator / Preview
=========================================================================
Estimates disk usage, GPU VRAM, capture duration, and frame count from
a ScenarioConfig without running the actual CARLA simulation.

Estimation model
----------------
Sensor KB/frame  (conservative upper bounds):
  rgb          120 KB
  lidar        200 KB
  radar          5 KB
  depth         96 KB
  semantic      80 KB
  instance      80 KB
  optical_flow  60 KB
  (per-frame labels/annotations)  2 KB
  (per-frame metadata)            1 KB

VRAM:
  CARLA base  1 500 MB
  + 256 MB per active sensor

FPS:
  Conservative estimate: 10 fps
  Vehicles add ~0.5 % overhead per vehicle to capture time
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from app.schemas.scenario import ScenarioConfig


# ── Sensor cost table (KB per frame) ─────────────────────────────────────────

_SENSOR_KB_PER_FRAME: dict[str, float] = {
    "rgb":          120.0,
    "lidar":        200.0,
    "radar":          5.0,
    "depth":         96.0,
    "semantic":      80.0,
    "instance":      80.0,
    "optical_flow":  60.0,
}

_LABELS_KB_PER_FRAME:   float = 2.0
_METADATA_KB_PER_FRAME: float = 1.0

_CARLA_BASE_VRAM_MB:    float = 1500.0
_PER_SENSOR_VRAM_MB:    float = 256.0
_BASE_FPS:              float = 10.0
_VEHICLE_OVERHEAD_PCT:  float = 0.005   # 0.5 % per vehicle


# ── Result model ──────────────────────────────────────────────────────────────

class ScenarioEstimate(BaseModel):
    estimated_duration_seconds: float
    estimated_disk_mb:          float
    estimated_gpu_vram_mb:      float
    estimated_frames_actual:    int
    cost_breakdown:             Dict[str, str]   # {"rgb": "60.0 MB", ...}
    performance_warnings:       List[str]


# ── Public API ────────────────────────────────────────────────────────────────

def estimate_scenario(cfg: ScenarioConfig) -> ScenarioEstimate:
    """
    Compute resource estimates for *cfg*.

    Does NOT mutate *cfg*.
    Returns a ScenarioEstimate.
    """
    frames = cfg.frames
    sensors = cfg.sensors or []
    total_vehicles = cfg.vehicles.total

    # ── Duration ─────────────────────────────────────────────────────────────
    vehicle_overhead = 1.0 + (total_vehicles * _VEHICLE_OVERHEAD_PCT)
    estimated_duration = (frames / _BASE_FPS) * vehicle_overhead

    # ── Disk usage ───────────────────────────────────────────────────────────
    breakdown_kb: dict[str, float] = {}

    for sensor in sensors:
        kb_per_frame = _SENSOR_KB_PER_FRAME.get(sensor, 0.0)
        breakdown_kb[sensor] = kb_per_frame * frames

    breakdown_kb["labels"]   = _LABELS_KB_PER_FRAME   * frames
    breakdown_kb["metadata"] = _METADATA_KB_PER_FRAME * frames

    total_kb   = sum(breakdown_kb.values())
    total_mb   = total_kb / 1024.0

    cost_breakdown: dict[str, str] = {
        k: f"{v / 1024.0:.1f} MB" for k, v in breakdown_kb.items()
    }

    # ── GPU VRAM ──────────────────────────────────────────────────────────────
    gpu_vram_mb = _CARLA_BASE_VRAM_MB + (len(sensors) * _PER_SENSOR_VRAM_MB)

    # ── Performance warnings ──────────────────────────────────────────────────
    perf_warnings: list[str] = []

    if total_vehicles > 200:
        perf_warnings.append(
            f"High vehicle count ({total_vehicles}) may reduce CARLA frame rate below {_BASE_FPS} FPS"
        )
    if len(sensors) >= 7:
        perf_warnings.append(
            f"{len(sensors)} sensors active — GPU VRAM usage will be high ({gpu_vram_mb:.0f} MB)"
        )
    if cfg.weather == "Fog" and "lidar" in sensors:
        perf_warnings.append("Fog weather reduces effective LiDAR range to ~30 m")
    if total_mb > 5000:
        perf_warnings.append(
            f"Estimated disk usage {total_mb:.0f} MB exceeds 5 GB — ensure sufficient storage"
        )

    return ScenarioEstimate(
        estimated_duration_seconds=round(estimated_duration, 2),
        estimated_disk_mb=round(total_mb, 2),
        estimated_gpu_vram_mb=round(gpu_vram_mb, 2),
        estimated_frames_actual=frames,
        cost_breakdown=cost_breakdown,
        performance_warnings=perf_warnings,
    )
