from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid
from datetime import datetime, timezone


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)

    # Status: queued | running | completed | failed
    status = Column(String, default="queued")
    progress = Column(Float, default=0.0)

    # Spec fields: map, sensors (list stored as JSON), frames
    map = Column(String, default="Town01")
    sensors = Column(JSON, default=lambda: ["rgb"])   # e.g. ["rgb", "lidar", "radar"]
    frames = Column(Integer, default=500)
    export_format = Column(String, default="kitti")   # e.g. "kitti", "coco", "nuscenes"

    output_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="jobs")
    dataset = relationship("Dataset", back_populates="job", uselist=False)
