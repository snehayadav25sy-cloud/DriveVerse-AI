"""
openai_provider.py — Build 3.6: OpenAI LLM Provider
=====================================================
Uses GPT-4o-mini to parse a free-text scenario description into a
ScenarioConfig. Reads OPENAI_API_KEY from the environment ONLY.

Set LLM_PROVIDER=openai and OPENAI_API_KEY=sk-... to activate.
"""

from __future__ import annotations

import json
import os

from app.schemas.scenario import ScenarioConfig
from app.services.llm_providers import LLMProvider


_SYSTEM_PROMPT = """
You are a simulation configuration expert for the DriveVerse AI autonomous vehicle
dataset platform. Your task is to extract a structured simulation scenario from the
user's natural language description.

You MUST respond with ONLY a valid JSON object matching this schema (no extra text):
{
  "schema_version": "3.1",
  "country": string or null,
  "city": string or null,
  "road_type": "Highway"|"City"|"Rural"|"Intersection"|"Residential"|"Suburban"|"Parking"|null,
  "weather": "Clear"|"Rain"|"Fog"|"Snow"|"Storm"|"Overcast"|null,
  "time_of_day": "Day"|"Night"|"Dusk"|"Dawn"|"Evening"|null,
  "lighting": "Default"|"Artificial"|"Overcast"|"Bright"|null,
  "traffic_density": "None"|"Light"|"Medium"|"Heavy"|"Gridlock"|null,
  "vehicles": {"car": int, "truck": int, "bus": int, "motorcycle": int, "bicycle": int, "van": int},
  "pedestrians": int,
  "sensors": ["rgb","lidar","radar","depth","semantic","instance","optical_flow"],
  "frames": int (1-2000),
  "export_format": "kitti"|"coco"|"nuscenes",
  "carla_map": "Town01"|"Town02"|"Town03"|null
}

Rules:
- sensors MUST contain at least "rgb"
- frames defaults to 500 if not specified
- export_format defaults to "kitti" if not specified
- Include ONLY sensors explicitly mentioned or implied
- Respond with ONLY the JSON object, no markdown, no explanation
"""


class OpenAIProvider(LLMProvider):
    """GPT-4o-mini backed provider."""

    def __init__(self) -> None:
        import openai  # lazy import — only fail if provider is selected
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it or use LLM_PROVIDER=regex instead."
            )
        self._client = openai.OpenAI(api_key=api_key)
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def name(self) -> str:
        return self._model

    @property
    def supports_optimization(self) -> bool:
        return False  # GPT already produces rich configs; skip optimizer

    @property
    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

    def parse(self, prompt: str) -> ScenarioConfig:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT.strip()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI returned invalid JSON: {exc}") from exc

        # Ensure sensors is not empty
        if not data.get("sensors"):
            data["sensors"] = ["rgb"]

        cfg = ScenarioConfig(**data)
        cfg.llm_provider = self.name
        cfg.source_prompt = prompt
        return cfg
