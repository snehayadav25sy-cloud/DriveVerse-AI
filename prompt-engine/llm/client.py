"""
prompt-engine/llm/client.py
============================
Build 3 — Phase 2: Provider-agnostic LLM wrapper

Reads LLM_API_KEY from environment ONLY — never hardcoded.
Supports OpenAI (active), with stubs for Gemini/Claude/Ollama.

To switch provider: set LLM_PROVIDER env var (default: openai).
"""
from __future__ import annotations

import os
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Load .env if present (does not override existing env vars)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / "gwm-platform" / "backend" / ".env",
                override=False)
except ImportError:
    pass  # dotenv optional

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "extract.txt"

def _load_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


# ── Abstract base ─────────────────────────────────────────────────────────────

class LLMClient(ABC):
    """Provider-agnostic interface: prompt → raw JSON string."""

    @abstractmethod
    def complete(self, user_prompt: str, system_prompt: str) -> str:
        """Return raw JSON string from the model. Raise on failure."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIClient(LLMClient):
    """
    Calls OpenAI Chat Completions API.
    Reads key from LLM_API_KEY environment variable.
    Model from LLM_MODEL (default: gpt-4o-mini).
    """

    def __init__(self):
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "LLM_API_KEY environment variable is not set. "
                "Export it before starting the server."
            )
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        self._client = OpenAI(api_key=api_key)
        self._model  = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    @property
    def provider_name(self) -> str:
        return f"openai/{self._model}"

    def complete(self, user_prompt: str, system_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content")
        return content


# ── Stubs (future providers) ─────────────────────────────────────────────────

class GeminiClient(LLMClient):
    @property
    def provider_name(self) -> str: return "gemini"
    def complete(self, user_prompt: str, system_prompt: str) -> str:
        raise NotImplementedError("Set GEMINI_API_KEY and implement GeminiClient")

class ClaudeClient(LLMClient):
    @property
    def provider_name(self) -> str: return "claude"
    def complete(self, user_prompt: str, system_prompt: str) -> str:
        raise NotImplementedError("Set ANTHROPIC_API_KEY and implement ClaudeClient")

class OllamaClient(LLMClient):
    @property
    def provider_name(self) -> str: return "ollama"
    def complete(self, user_prompt: str, system_prompt: str) -> str:
        raise NotImplementedError("Set OLLAMA_HOST and implement OllamaClient")


# ── Factory ───────────────────────────────────────────────────────────────────

def get_client() -> LLMClient:
    """Return the active LLM client based on LLM_PROVIDER env var."""
    provider = os.environ.get("LLM_PROVIDER", "openai").lower().strip()
    match provider:
        case "openai":  return OpenAIClient()
        case "gemini":  return GeminiClient()
        case "claude":  return ClaudeClient()
        case "ollama":  return OllamaClient()
        case _:
            log.warning(f"Unknown LLM_PROVIDER '{provider}', defaulting to openai")
            return OpenAIClient()
