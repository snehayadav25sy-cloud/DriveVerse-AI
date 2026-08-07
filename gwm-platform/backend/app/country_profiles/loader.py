import os
import yaml
from typing import Dict, Any
from app.country_profiles.models import CountryProfile

class CountryProfileLoader:
    def __init__(self, countries_dir: str):
        self.countries_dir = countries_dir

    def _resolve_file_path(self, country_id: str) -> str:
        # Standard filenames: india.yaml, mumbai.yaml, etc.
        filename = f"{country_id.lower().strip()}.yaml"
        return os.path.join(self.countries_dir, filename)

    def load_raw_dict(self, country_id: str) -> Dict[str, Any]:
        path = self._resolve_file_path(country_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Country profile file not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not data:
                return {}
            return data

    def load_profile(self, country_id: str) -> CountryProfile:
        """
        Loads the YAML profile, resolving inheritance recursions if 'extends' is declared.
        """
        raw = self.load_raw_dict(country_id)
        
        # Check inheritance
        parent_id = raw.get("extends")
        if parent_id:
            # Recursively load parent
            parent_profile = self.load_profile(parent_id)
            parent_dict = parent_profile.model_dump()
            
            # Perform deep merge: override parent_dict with raw
            merged = self._deep_merge(parent_dict, raw)
            
            # Ensure ID remains the child ID, extends remains parent ID
            merged["id"] = raw.get("id", country_id)
            merged["extends"] = parent_id
            
            return CountryProfile(**merged)
            
        return CountryProfile(**raw)

    def _deep_merge(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merges overrides dict into base dict.
        """
        result = dict(base)
        for key, value in overrides.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
