"""
backend/app/models/world.py — Build 6: World generation DB models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime, timezone
import uuid


class WorldPlan(Base):
    __tablename__ = "world_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, unique=True)
    world_id = Column(String, nullable=False, index=True)
    world_seed = Column(Integer, nullable=False)
    location_query = Column(String, nullable=False)
    country = Column(String, nullable=False)
    map_name = Column(String, nullable=False)
    plan_json = Column(JSON, nullable=False)
    plan_hash = Column(String, nullable=False)
    asset_resolution_stats = Column(JSON, nullable=True)
    fallbacks = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="world_plan")
    provenance = relationship("WorldProvenance", back_populates="world_plan", uselist=False)
    artifacts = relationship("WorldArtifact", back_populates="world_plan")


class WorldProvenance(Base):
    __tablename__ = "world_provenance"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    world_plan_id = Column(String, ForeignKey("world_plans.id"), nullable=False, unique=True)
    build_version = Column(String, nullable=False)
    country_profile_hash = Column(String, nullable=False)
    geography_hash = Column(String, nullable=False)
    world_plan_hash = Column(String, nullable=False)
    asset_registry_hash = Column(String, nullable=False)
    world_seed = Column(Integer, nullable=False)
    traffic_seed = Column(Integer, nullable=False)
    pedestrian_seed = Column(Integer, nullable=False)
    weather_seed = Column(Integer, nullable=False)
    asset_seed = Column(Integer, nullable=False)
    scenario_seed = Column(Integer, nullable=False)
    carla_version = Column(String, nullable=False)
    git_commit = Column(String, nullable=True)
    provenance_hash = Column(String, nullable=False)
    fallbacks = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world_plan = relationship("WorldPlan", back_populates="provenance")


class WorldArtifact(Base):
    __tablename__ = "world_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    world_plan_id = Column(String, ForeignKey("world_plans.id"), nullable=False)
    artifact_type = Column(String, nullable=False)
    artifact_path = Column(String, nullable=True)
    artifact_size_bytes = Column(Integer, nullable=True)
    artifact_hash = Column(String, nullable=True)
    artifact_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    world_plan = relationship("WorldPlan", back_populates="artifacts")
