from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid
from datetime import datetime, timezone


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)

    # Build 2: sensors list + per-sensor metadata JSON for traceability
    sensors = Column(JSON, default=lambda: ["rgb"])   # e.g. ["rgb", "lidar"]
    sensor_metadata = Column(JSON, nullable=True)     # e.g. {"lidar_channels": 32, "radar_range": 100}
    path = Column(String, nullable=False)
    frame_count = Column(Integer, default=0)
    
    # Counts and format tracking
    rgb_count = Column(Integer, default=0)
    lidar_count = Column(Integer, default=0)
    annotation_count = Column(Integer, default=0)
    export_format = Column(String, default="kitti")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="dataset")
