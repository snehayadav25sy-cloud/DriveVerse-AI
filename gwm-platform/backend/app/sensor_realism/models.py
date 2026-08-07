"""
app/sensor_realism/models.py — Build 6: Sensor realism configuration models
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class RGBConfig(BaseModel):
    resolution: Tuple[int, int] = (1280, 720)
    fov: float = Field(90.0, ge=10.0, le=180.0)
    exposure: float = Field(0.0, ge=-5.0, le=5.0)
    brightness: float = Field(0.0, ge=-1.0, le=1.0)
    motion_blur: float = Field(0.0, ge=0.0, le=1.0)
    noise_level: float = Field(0.0, ge=0.0, le=1.0)


class LiDARConfig(BaseModel):
    channels: int = Field(32, ge=1, le=128)
    range_m: float = Field(100.0, gt=0.0)
    rotation_frequency: float = Field(10.0, gt=0.0)
    points_per_second: int = Field(100000, gt=0.0)
    dropout_probability: float = Field(0.0, ge=0.0, le=1.0)
    range_noise: float = Field(0.0, ge=0.0, le=5.0)


class RadarConfig(BaseModel):
    range_m: float = Field(100.0, gt=0.0)
    velocity_noise: float = Field(0.0, ge=0.0, le=10.0)
    azimuth_noise: float = Field(0.0, ge=0.0, le=0.1)
    dropout_probability: float = Field(0.0, ge=0.0, le=1.0)


class DepthConfig(BaseModel):
    depth_noise: float = Field(0.0, ge=0.0, le=5.0)
    max_range: float = Field(100.0, gt=0.0)
    invalid_pixel_probability: float = Field(0.0, ge=0.0, le=1.0)


class SensorRealismConfig(BaseModel):
    rgb: RGBConfig = Field(default_factory=RGBConfig)
    lidar: LiDARConfig = Field(default_factory=LiDARConfig)
    radar: RadarConfig = Field(default_factory=RadarConfig)
    depth: DepthConfig = Field(default_factory=DepthConfig)
