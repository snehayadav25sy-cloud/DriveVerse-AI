from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DatasetResponse(BaseModel):
    id: str
    job_id: str
    sensors: List[str]
    sensor_metadata: Optional[Any] = None
    path: str
    frame_count: int
    rgb_count: int
    lidar_count: int
    annotation_count: int
    export_format: str
    created_at: datetime

    class Config:
        from_attributes = True
