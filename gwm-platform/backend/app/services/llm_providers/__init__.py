"""
llm_providers/__init__.py — Build 3.6: LLM Provider Abstract Base
===================================================================
Abstract interface that every concrete LLM provider must implement.
Swap providers by changing LLM_PROVIDER env var — zero API changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.scenario import ScenarioConfig


class LLMProvider(ABC):
    """Abstract base for all prompt-parsing LLM backends."""

    @abstractmethod
    def parse(self, prompt: str) -> ScenarioConfig:
        """Parse a free-text prompt into a ScenarioConfig."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name, e.g. 'regex', 'gpt-4o-mini'."""
        ...

    @property
    def supports_optimization(self) -> bool:
        """Whether this provider has its own optimization pass."""
        return False

    @property
    def is_available(self) -> bool:
        """Whether the provider is currently usable (key set, server up, etc.)."""
        return True

    def health(self) -> dict:
        return {"provider": self.name, "available": self.is_available}
