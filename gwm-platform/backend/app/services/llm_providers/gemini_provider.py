"""
gemini_provider.py — Build 3.6: Google Gemini Provider (stub)
=============================================================
Stub implementation. Set LLM_PROVIDER=gemini and GEMINI_API_KEY to activate.
"""
from __future__ import annotations
import os
from app.schemas.scenario import ScenarioConfig
from app.services.llm_providers import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini-backed provider (stub — activate when GEMINI_API_KEY is set)."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return bool(os.environ.get("GEMINI_API_KEY"))

    def parse(self, prompt: str) -> ScenarioConfig:
        raise NotImplementedError(
            "GeminiProvider is not yet implemented. "
            "Set LLM_PROVIDER=regex or LLM_PROVIDER=openai instead."
        )
