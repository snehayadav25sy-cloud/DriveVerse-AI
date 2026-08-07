import os
import shutil
import yaml
from typing import Dict, List, Optional
from app.country_profiles.models import CountryProfile
from app.country_profiles.loader import CountryProfileLoader

class CountryProfileRegistry:
    def __init__(self, countries_dir: str):
        self.countries_dir = countries_dir
        self.loader = CountryProfileLoader(countries_dir)
        self.profiles: Dict[str, CountryProfile] = {}
        # Auto-load on startup
        self.reload_all()

    def reload_all(self):
        """
        Scans the countries_dir directory and loads all .yaml files.
        """
        self.profiles.clear()
        if not os.path.exists(self.countries_dir):
            os.makedirs(self.countries_dir, exist_ok=True)
            return

        # Load independent profiles first, then inherited profiles
        raw_files = [f for f in os.listdir(self.countries_dir) if f.endswith(".yaml")]
        
        # Parse all raw dicts to resolve load order
        loaded_raw = {}
        for f in raw_files:
            c_id = f[:-5] # remove '.yaml'
            try:
                raw_dict = self.loader.load_raw_dict(c_id)
                loaded_raw[c_id] = raw_dict
            except Exception as e:
                print(f"Error reading YAML file {f}: {e}")

        # Resolve inheritance load sequence
        # We load parent profiles first so the loader can find them in self.profiles
        loaded_count = 0
        iterations = 0
        while len(loaded_raw) > 0 and iterations < 10:
            iterations += 1
            to_remove = []
            for c_id, raw_dict in list(loaded_raw.items()):
                parent = raw_dict.get("extends")
                # If it doesn't inherit, or the parent is already registered in registry
                if not parent or parent in self.profiles:
                    try:
                        profile = self.loader.load_profile(c_id)
                        self.profiles[profile.id.lower().strip()] = profile
                        to_remove.append(c_id)
                    except Exception as e:
                        print(f"Error compilation loading profile '{c_id}': {e}")
                        # Remove to avoid infinite loop
                        to_remove.append(c_id)
            for c_id in to_remove:
                if c_id in loaded_raw:
                    del loaded_raw[c_id]

    def get_profile(self, country_id: str) -> Optional[CountryProfile]:
        key = country_id.lower().strip()
        if key in self.profiles:
            return self.profiles[key]
        return None

    def list_profiles(self) -> List[CountryProfile]:
        return list(self.profiles.values())

    def save_profile(self, profile: CountryProfile, yaml_content: str = None) -> str:
        """
        Saves or updates a country profile. Writes it back to the yaml file.
        """
        c_id = profile.id.lower().strip()
        self.profiles[c_id] = profile
        
        file_path = os.path.join(self.countries_dir, f"{c_id}.yaml")
        
        if yaml_content:
            # Save raw custom YAML from UI/API
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
        else:
            # Serialize object to YAML
            # Convert profile to dict
            p_dict = profile.model_dump(exclude_none=True)
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(p_dict, f, default_flow_style=False, sort_keys=False)
                
        # Reload to refresh inheritance trees
        self.reload_all()
        return file_path

    def delete_profile(self, country_id: str) -> bool:
        c_id = country_id.lower().strip()
        if c_id in self.profiles:
            del self.profiles[c_id]
            file_path = os.path.join(self.countries_dir, f"{c_id}.yaml")
            if os.path.exists(file_path):
                os.remove(file_path)
            # Reload to refresh inheritance trees
            self.reload_all()
            return True
        return False
