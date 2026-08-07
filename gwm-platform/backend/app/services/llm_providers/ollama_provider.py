"""
ollama_provider.py — Build 3.6: Ollama Local Provider (stub)
=============================================================
Stub implementation. Set LLM_PROVIDER=ollama and OLLAMA_HOST to activate.
"""
from __future__ import annotations
import os
from app.schemas.scenario import ScenarioConfig
from app.services.llm_providers import LLMProvider


class OllamaProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        return bool(os.environ.get("OLLAMA_HOST"))

    def parse(self, prompt: str) -> ScenarioConfig:
        raise NotImplementedError(
            "OllamaProvider is not yet implemented. "
            "Set LLM_PROVIDER=regex instead."
        )
