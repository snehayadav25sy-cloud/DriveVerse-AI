"""
factory.py — Build 3.6: LLM Provider Factory
=============================================
Reads LLM_PROVIDER environment variable and returns the appropriate provider.
Default: regex (zero-dependency, always works)
"""

from __future__ import annotations

import os

from app.services.llm_providers import LLMProvider


def get_provider() -> LLMProvider:
    """
    Return the active LLM provider based on LLM_PROVIDER env var.

    Supported values:
      regex   (default) — rule-based, no API key needed
      openai             — GPT-4o-mini, requires OPENAI_API_KEY
      gemini             — Google Gemini, requires GEMINI_API_KEY  (stub)
      claude             — Anthropic Claude, requires ANTHROPIC_API_KEY (stub)
      ollama             — Local Ollama, requires OLLAMA_HOST (stub)
    """
    name = os.getenv("LLM_PROVIDER", "regex").lower().strip()

    if name == "openai":
        from app.services.llm_providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if name == "gemini":
        from app.services.llm_providers.gemini_provider import GeminiProvider
        return GeminiProvider()

    if name == "claude":
        from app.services.llm_providers.claude_provider import ClaudeProvider
        return ClaudeProvider()

    if name == "ollama":
        from app.services.llm_providers.ollama_provider import OllamaProvider
        return OllamaProvider()

    # Default: regex
    from app.services.llm_providers.regex_provider import RegexProvider
    return RegexProvider()


def get_provider_info() -> dict:
    """Return metadata about the active provider (safe to expose via API)."""
    try:
        provider = get_provider()
        return {
            "provider": provider.name,
            "available": provider.is_available,
            "supports_optimization": provider.supports_optimization,
            "env_key": os.getenv("LLM_PROVIDER", "regex"),
        }
    except Exception as exc:
        return {
            "provider": "unavailable",
            "available": False,
            "supports_optimization": False,
            "error": str(exc),
            "env_key": os.getenv("LLM_PROVIDER", "regex"),
        }
