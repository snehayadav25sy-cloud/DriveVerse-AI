"""
claude_provider.py — Build 3.6: Anthropic Claude Provider (stub)
=================================================================
Stub implementation. Set LLM_PROVIDER=claude and ANTHROPIC_API_KEY to activate.
"""
from __future__ import annotations
import os
from app.schemas.scenario import ScenarioConfig
from app.services.llm_providers import LLMProvider


class ClaudeProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "claude"

    @property
    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def parse(self, prompt: str) -> ScenarioConfig:
        raise NotImplementedError(
            "ClaudeProvider is not yet implemented. "
            "Set LLM_PROVIDER=regex or LLM_PROVIDER=openai instead."
        )
