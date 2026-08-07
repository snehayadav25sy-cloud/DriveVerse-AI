from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

VALID_MAPS    = {"Town01", "Town02", "Town03", "Town04", "Town05", "Town06", "Town07", "Town10HD"}
VALID_SENSORS = {
    "rgb", "lidar", "radar", "depth", "semantic", "instance", "optical_flow",
    "camera_front", "camera_left", "camera_right", "camera_rear"
}
VALID_FORMATS = {"kitti", "coco", "nuscenes"}


class JobCreate(BaseModel):
    project_id: str
    map: str = "Town01"
    sensors: List[str] = ["rgb"]
    frames: int = 500
    export_format: str = "kitti"

    @validator("map")
    def validate_map(cls, v):
        if v not in VALID_MAPS:
            raise ValueError(f"map must be one of {sorted(VALID_MAPS)}")
        return v

    @validator("export_format")
    def validate_export_format(cls, v):
        v = v.lower()
        if v not in VALID_FORMATS:
            raise ValueError(f"export_format must be one of {sorted(VALID_FORMATS)}")
        return v

    @validator("sensors", each_item=True)
    def validate_each_sensor(cls, v):
        v = v.lower()
        if v not in VALID_SENSORS:
            raise ValueError(f"each sensor must be one of {sorted(VALID_SENSORS)}")
        return v

    @validator("sensors")
    def validate_sensors_nonempty(cls, v):
        if not v:
            raise ValueError("sensors must contain at least one value")
        return list(set(v))  # deduplicate while preserving valid entries

    @validator("frames")
    def validate_frames(cls, v):
        if v < 1 or v > 2000:
            raise ValueError("frames must be between 1 and 2000")
        return v


class JobResponse(BaseModel):
    id: str
    project_id: str
    status: str
    progress: float
    map: str
    sensors: List[str]
    frames: int
    export_format: str
    output_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
