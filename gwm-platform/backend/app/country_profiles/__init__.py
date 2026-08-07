import os
from app.country_profiles.models import CountryProfile, RealityScenario, ResolvedScenario, Provenance
from app.country_profiles.registry import CountryProfileRegistry
from app.country_profiles.compiler import CountryCompiler

# Initialize global registry pointing to countries/ folder
DEFAULT_COUNTRIES_DIR = os.path.join(os.path.dirname(__file__), "countries")
registry = CountryProfileRegistry(DEFAULT_COUNTRIES_DIR)
compiler = CountryCompiler(registry)

__all__ = [
    "CountryProfile",
    "RealityScenario",
    "ResolvedScenario",
    "Provenance",
    "CountryProfileRegistry",
    "CountryCompiler",
    "registry",
    "compiler"
]
