from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel

from app.country_profiles import registry, compiler
from app.country_profiles.models import RealityScenario, CountryProfile

router = APIRouter(prefix="/countries", tags=["Country Profiles"])


# ── Request/Response Models ────────────────────────────────────────────────────

class ScenarioExpandRequest(BaseModel):
    country: str
    weather: str = "sunny"
    traffic: str = "normal"
    time_of_day: str = "noon"
    road_type: str = "highway"
    modifiers: List[str] = []


class ScenarioExpandResponse(BaseModel):
    resolved_scenario: dict
    provenance: dict
    warnings: List[str]


class ProfileSaveRequest(BaseModel):
    yaml_content: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/", summary="List all active country profiles")
def list_countries():
    """
    Returns a list of all loaded country profiles with id, version, drive_side,
    and vehicle_mix summary.
    """
    profiles = registry.list_profiles()
    return [
        {
            "id": p.id,
            "version": p.version,
            "drive_side": p.rules.drive_side,
            "vehicle_classes": list(p.vehicle_mix.keys()),
            "weather_presets": list(p.weather_presets.keys()),
            "supports": p.supports.model_dump()
        }
        for p in profiles
    ]


@router.get("/{country_id}", summary="Get a specific country profile")
def get_country(country_id: str):
    """
    Returns the full country profile for a given country ID.
    """
    profile = registry.get_profile(country_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Country profile '{country_id}' not found")
    return profile.model_dump()


@router.post("/", summary="Add a custom country profile from YAML")
def create_country(request: ProfileSaveRequest):
    """
    Saves a custom country profile from raw YAML content.
    The YAML must have at minimum a valid 'id' field.
    """
    import yaml as _yaml
    try:
        raw = _yaml.safe_load(request.yaml_content)
        if not raw or "id" not in raw:
            raise HTTPException(status_code=400, detail="YAML must contain an 'id' field")
        profile = CountryProfile(**raw)
        saved_path = registry.save_profile(profile, yaml_content=request.yaml_content)
        return {"status": "created", "id": profile.id, "path": saved_path}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse country profile: {e}")


@router.put("/{country_id}", summary="Update an existing country profile from YAML")
def update_country(country_id: str, request: ProfileSaveRequest):
    """
    Replaces an existing country profile from raw YAML content.
    """
    import yaml as _yaml
    existing = registry.get_profile(country_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Country profile '{country_id}' not found")
    try:
        raw = _yaml.safe_load(request.yaml_content)
        if not raw:
            raise HTTPException(status_code=400, detail="Empty YAML content")
        raw["id"] = country_id  # Ensure ID cannot be changed via body
        profile = CountryProfile(**raw)
        saved_path = registry.save_profile(profile, yaml_content=request.yaml_content)
        return {"status": "updated", "id": country_id, "path": saved_path}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to update country profile: {e}")


@router.delete("/{country_id}", summary="Delete a country profile")
def delete_country(country_id: str):
    """
    Deletes a country profile and removes its YAML file.
    """
    success = registry.delete_profile(country_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Country profile '{country_id}' not found")
    return {"status": "deleted", "id": country_id}


@router.post("/scenario/expand", summary="Compile a reality scenario to a fully resolved simulation JSON")
def expand_scenario(request: ScenarioExpandRequest):
    """
    Translates a high-level RealityScenario (Country, Weather, Traffic)
    into a fully resolved simulation configuration JSON, including:
    - Resolved weather parameters
    - Blueprint-resolved vehicle mix
    - Difficulty & quality scores
    - Provenance fingerprint (hashes, seeds, versions)
    """
    reality = RealityScenario(
        country=request.country,
        weather=request.weather,
        traffic=request.traffic,
        time_of_day=request.time_of_day,
        road_type=request.road_type,
        modifiers=request.modifiers
    )
    try:
        resolved, provenance = compiler.compile_scenario(reality)
        return ScenarioExpandResponse(
            resolved_scenario=resolved.model_dump(),
            provenance=provenance,
            warnings=resolved.warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario compilation failed: {e}")
