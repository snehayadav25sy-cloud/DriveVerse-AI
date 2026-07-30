"""
backend/app/models/prompt.py
==============================
Build 3 — Phase 5: Prompt history & revision DB models

Tables:
  prompts   — stores each user prompt submission
  scenarios — stores the parsed ScenarioConfig JSON for each prompt
  revisions — stores each refinement (additive, not destructive)
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Prompt(Base):
    __tablename__ = "prompts"

    id         = Column(String, primary_key=True, default=_uuid)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    text       = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    scenario   = relationship("Scenario", back_populates="prompt", uselist=False,
                              cascade="all, delete-orphan")


class Scenario(Base):
    __tablename__ = "scenarios"

    id           = Column(String, primary_key=True, default=_uuid)
    prompt_id    = Column(String, ForeignKey("prompts.id"), nullable=False, unique=True)
    scenario_json = Column(JSON, nullable=False)   # serialized ScenarioConfig dict
    llm_provider = Column(String, nullable=True)
    job_id       = Column(String, ForeignKey("jobs.id"), nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    prompt    = relationship("Prompt", back_populates="scenario")
    revisions = relationship("Revision", back_populates="scenario",
                             cascade="all, delete-orphan",
                             order_by="Revision.version")


class Revision(Base):
    __tablename__ = "revisions"

    id           = Column(String, primary_key=True, default=_uuid)
    scenario_id  = Column(String, ForeignKey("scenarios.id"), nullable=False, index=True)
    version      = Column(Integer, nullable=False)       # 1-based, monotonic
    refinement   = Column(Text, nullable=True)           # the refinement prompt text
    scenario_json = Column(JSON, nullable=False)          # full scenario state at this version
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    scenario = relationship("Scenario", back_populates="revisions")
