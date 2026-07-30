from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database.database import Base
import uuid
from datetime import datetime, timezone


class PromptHistory(Base):
    """
    Build 3.5 — Prompt History DB
    Stores every raw prompt text, the parsed ScenarioConfig JSON, and an
    optional reference to the Job that was created from this prompt.
    """
    __tablename__ = 'prompt_history'

    id          = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id     = Column(String, ForeignKey('users.id'), nullable=False)
    prompt_text = Column(Text, nullable=False)
    scenario_json = Column(JSON, nullable=True)
    job_id      = Column(String, ForeignKey('jobs.id'), nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', backref='prompt_history')
