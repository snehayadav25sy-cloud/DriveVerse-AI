"""
regex_provider.py — Build 3.6: Regex LLM Provider
===================================================
Wraps the existing rule-based prompt_parser.py as a proper LLMProvider.
Zero external dependencies. Default provider when LLM_PROVIDER is unset.
"""

from __future__ import annotations

from app.schemas.scenario import ScenarioConfig
from app.services.llm_providers import LLMProvider
from app.services.prompt_parser import parse_prompt


class RegexProvider(LLMProvider):
    """Rule-based NLP parser — no external API required."""

    @property
    def name(self) -> str:
        return "regex"

    @property
    def supports_optimization(self) -> bool:
        return True  # regex provider uses prompt_optimizer.py

    def parse(self, prompt: str) -> ScenarioConfig:
        return parse_prompt(prompt)
