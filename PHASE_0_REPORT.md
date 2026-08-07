# Phase 0 — Repository Inspection Report
Build 5 — Geography Engine v1.0

====================================================================
A. CURRENT ARCHITECTURE DIAGRAM (text)
====================================================================

USER
 │
 ▼
REACT FRONTEND (Port 80)
 │   - Dashboard, GenerateDataset, GeneratePrompt, Jobs, Quality, CountryProfiles
 │   - TanStack Query, React Router, Tailwind CSS
 │
 ▼
FASTAPI BACKEND (Port 8000)
 │   - REST API: auth, projects, jobs, datasets, analytics, prompt, countries
 │   - SQLAlchemy ORM → PostgreSQL (Docker) / SQLite (fallback)
 │
 ├── Build 3: Prompt Engine
 │   └── LLM → ScenarioConfig (Pydantic v2)
 │       └── validate → optimize → translate → preview → refine
 │
 ├── Build 4: Country Profile Engine
 │   └── YAML profiles → compiler → ResolvedScenario
 │       └── weather, traffic rules, vehicle mix, blueprint resolver
 │
 └── Build 5 (NEW): Geography Engine
     └── Geocoder → OSM → RoadGraph → OpenDRIVE → CARLA
 │
 ▼
WORKER (CARLA 0.9.16)
 │   - connect (version-checked)
 │   - load_simulation_map
 │   - spawn_ego_vehicle + background traffic + pedestrians
 │   - MultiSensorCapture (synchronous mode)
 │   - Population system (Traffic Manager)
 │
 ▼
CARLA SIMULATOR (C:\carla\WindowsNoEditor\CarlaUE4.exe)
 │   - sensor.camera.rgb
 │   - sensor.lidar.ray_cast
 │   - sensor.other.radar
 │   - depth, semantic, instance, optical_flow cameras
 │
 ▼
DATASET-ENGINE
 │   - capture (RGB, LiDAR, radar, depth, semantic, instance, optical_flow)
 │   - annotations (classify, track, bbox projection)
 │   - calibration (intrinsics, extrinsics)
 │   - metadata (per-frame JSON)
 │   - exporters (internal, KITTI, COCO, nuScenes)
 │
 ▼
STORAGE
 │   - gwm-platform/storage/ → dataset_{uuid}.zip
 │   - Contains: images/, pointcloud/, labels/, metadata/, calibration/
 │   - Plus Build 4: resolved_scenario.json, country_profile.json, etc.
 │
 ▼
DATABASE (PostgreSQL / SQLite)
 │   - users, projects, jobs, datasets
 │   - prompts, scenarios, revisions (Build 3)

====================================================================
B. LIST OF EXISTING RELEVANT FILES WITH PATHS
====================================================================

Backend API:
  gwm-platform/backend/app/api/auth.py
  gwm-platform/backend/app/api/projects.py
  gwm-platform/backend/app/api/jobs.py
  gwm-platform/backend/app/api/datasets.py
  gwm-platform/backend/app/api/analytics.py
  gwm-platform/backend/app/api/prompt.py
  gwm-platform/backend/app/api/countries.py

Backend Models:
  gwm-platform/backend/app/models/user.py
  gwm-platform/backend/app/models/project.py
  gwm-platform/backend/app/models/job.py
  gwm-platform/backend/app/models/dataset.py
  gwm-platform/backend/app/models/prompt.py

Backend Schemas:
  gwm-platform/backend/app/schemas/user.py
  gwm-platform/backend/app/schemas/project.py
  gwm-platform/backend/app/schemas/job.py
  gwm-platform/backend/app/schemas/dataset.py
  gwm-platform/backend/app/schemas/scenario.py

Backend Services:
  gwm-platform/backend/app/services/prompt_parser.py
  gwm-platform/backend/app/services/prompt_validator.py
  gwm-platform/backend/app/services/prompt_optimizer.py
  gwm-platform/backend/app/services/scenario_translator.py
  gwm-platform/backend/app/services/scenario_estimator.py
  gwm-platform/backend/app/services/llm_providers/{factory,openai,gemini,claude,ollama,regex}_provider.py

Backend Country Profiles:
  gwm-platform/backend/app/country_profiles/__init__.py
  gwm-platform/backend/app/country_profiles/models.py
  gwm-platform/backend/app/country_profiles/compiler.py
  gwm-platform/backend/app/country_profiles/registry.py
  gwm-platform/backend/app/country_profiles/resolver.py
  gwm-platform/backend/app/country_profiles/loader.py
  gwm-platform/backend/app/country_profiles/rules.py
  gwm-platform/backend/app/country_profiles/weather.py
  gwm-platform/backend/app/country_profiles/defaults.py
  gwm-platform/backend/app/country_profiles/capabilities.yaml
  gwm-platform/backend/app/country_profiles/countries/{usa,japan,india,dubai,germany,uk,mumbai}.yaml

Backend Main:
  gwm-platform/backend/main.py
  gwm-platform/backend/database/database.py
  gwm-platform/backend/Dockerfile
  gwm-platform/backend/requirements.txt

Worker:
  gwm-platform/worker/main.py
  gwm-platform/worker/Dockerfile
  gwm-platform/worker/simulator/carla/client.py
  gwm-platform/worker/simulator/carla/maps.py
  gwm-platform/worker/simulator/carla/vehicle.py
  gwm-platform/worker/simulator/carla/camera.py
  gwm-platform/worker/simulator/carla/lidar.py
  gwm-platform/worker/simulator/carla/radar.py
  gwm-platform/worker/simulator/carla/capture.py
  gwm-platform/worker/simulator/carla/population.py
  gwm-platform/worker/simulator/carla/sync_engine.py
  gwm-platform/worker/simulator/sensors/{depth_camera,instance_camera,optical_flow,semantic_camera,radar}.py

Dataset-Engine:
  gwm-platform/dataset-engine/capture/{rgb,lidar}.py
  gwm-platform/dataset-engine/annotations/{classify,tracking,bbox,class_mapping}.py
  gwm-platform/dataset-engine/calibration/{intrinsics,extrinsics}.py
  gwm-platform/dataset-engine/exporters/{internal,kitti,coco/export,nuscenes/export,class_mapping_kitti}.py
  gwm-platform/dataset-engine/metadata/frame_metadata.py
  gwm-platform/dataset-engine/tests/test_phase1.py

Prompt-Engine:
  prompt-engine/llm/client.py
  prompt-engine/parser/parser.py
  prompt-engine/schemas/scenario_schema.py
  prompt-engine/schemas/test_scenario_schema.py
  prompt-engine/templates/extract.txt
  prompt-engine/validators/validator.py

Frontend:
  gwm-platform/frontend/src/App.tsx
  gwm-platform/frontend/src/pages/{Dashboard,GenerateDataset,GeneratePrompt,Jobs,Projects,DatasetQuality,CountryProfiles,Login,Register}.tsx
  gwm-platform/frontend/src/components/{GenerateForm,PromptBar,Sidebar,Navbar,JobTable,CountryCard,ScenarioCard,...}.tsx
  gwm-platform/frontend/src/services/{api,countries,datasets,generator,prompt,quality,jobs}.ts
  gwm-platform/frontend/src/types/index.ts
  gwm-platform/frontend/package.json
  gwm-platform/frontend/Dockerfile

Docker/Config:
  docker-compose.yml
  Dockerfile.backend
  requirements.txt
  requirements-carla.txt
  AGENTS.md
  README.md

====================================================================
C. EXISTING BUILD 3 INTERFACE SIGNATURES
====================================================================

ScenarioConfig (gwm-platform/backend/app/schemas/scenario.py):
  schema_version: str = "3.1"
  country: Optional[str] = None
  city: Optional[str] = None
  road_type: Optional[str] = None
  modifiers: List[str] = []
  weather: Optional[str] = None
  time_of_day: Optional[str] = None
  lighting: Optional[str] = None
  traffic_density: Optional[str] = None
  vehicles: VehicleMix = Field(default_factory=VehicleMix)
  pedestrians: int = Field(0, ge=0)
  sensors: List[str] = Field(default_factory=lambda: ["rgb"])
  frames: int = Field(500, ge=1, le=2000)
  export_format: str = Field("kitti", pattern="^(kitti|coco|nuscenes)$")
  carla_map: Optional[str] = None
  optimizer_applied: bool = False
  validation_passed: bool = False
  confidence: Dict[str, float] = {}
  explanation: List[str] = []
  unrecognised_tokens: List[str] = []
  source_prompt: Optional[str] = None
  llm_provider: Optional[str] = None
  validation: Optional[ValidationResult] = None
  optimizer_changes: List[OptimizerChange] = []
  translation: Optional[TranslationResult] = None

  to_job_params() → dict with keys: map, sensors, frames, export_format

parse_prompt(prompt: str) → ScenarioConfig
  Raises: ValueError, RuntimeError, ValidationError

validate_scenario(cfg, source_prompt) → ValidationResult
optimize_scenario(cfg) → None
translate_scenario(cfg) → None (mutates cfg.carla_map)
estimate_scenario(cfg) → ScenarioEstimate

====================================================================
D. EXISTING BUILD 4 INTERFACE SIGNATURES
====================================================================

CountryProfile (app/country_profiles/models.py):
  id: str
  version: str = "1.0.0"
  schema_version: int = 1
  extends: Optional[str] = None
  author: str = "DriveVerse"
  updated: str
  supports: SupportsFlags (auto_rickshaw, tram, train, snow_accumulation, deformable_terrain)
  rules: TrafficRules (drive_side, speed_limits, signal_duration_s, behavior)
  weather_presets: Dict[str, WeatherPreset]
  vehicle_mix: Dict[str, float]
  pedestrians: PedestrianSettings (density, walking_speed)

RealityScenario:
  country: str = "usa"
  weather: str = "sunny"
  traffic: str = "normal"
  time_of_day: str = "noon"
  road_type: str = "highway"
  modifiers: List[str] = []

ResolvedScenario:
  drive_side: str = "right"
  weather: ResolvedWeather
  vehicles: Dict[str, float]
  pedestrians: PedestrianSettings
  speed_limits: SpeedLimits
  behavior: DriverBehavior
  difficulty_score: float
  quality_score: float
  warnings: List[str]

ResolvedWeather:
  precipitation, cloudiness, precipitation_deposits, wind_intensity,
  fog_density, fog_distance, sun_altitude_angle, sun_azimuth_angle, wetness

Provenance:
  prompt_hash, scenario_hash, compiler_version, country_profile,
  carla_version, git_commit, seeds

registry.get_profile(country_id) → CountryProfile | None
registry.list_profiles() → List[CountryProfile]
compiler.compile_scenario(reality) → (ResolvedScenario, dict provenance)
resolver.resolve_blueprint_mix(vehicle_mix) → (Dict[str,float], List[str])

====================================================================
E. EXISTING CARLA ADAPTER CODE
====================================================================

client.py:
  connect(host=None, port=2000, timeout=60.0) → (client, world)
    - REQUIRED_VERSION = "0.9.16"
    - Checks installed carla package version == REQUIRED_VERSION
    - Checks server_version == REQUIRED_VERSION
    - Retries get_world() with 2s sleep, up to timeout seconds
    - client.set_timeout(30.0) after successful get_world
  disconnect(client, actors) → destroys all actors in list

maps.py:
  load_simulation_map(client, map_name="Town01") → world
    - Sleeps 3s warmup
    - Checks if map already loaded
    - client.load_world(map_name) if different
    - Sleeps 5s after load

vehicle.py:
  spawn_ego_vehicle(world, vehicle_filter="vehicle.tesla.model3") → vehicle
    - Falls back to vehicle.* if specific blueprint not found
    - Enables autopilot

camera.py:
  attach_rgb_camera(world, vehicle) → camera actor
    - 1280x720, FOV 90, sensor_tick 0.1
    - Mount: x=1.5, y=0, z=1.4, pitch=0, yaw=0, roll=0

lidar.py:
  attach_lidar(world, vehicle, channels=32, range_m=100.0, rotation_frequency=10.0, points_per_second=100000) → lidar actor
    - Mount: x=0, y=0, z=2.5

radar.py:
  attach_radar(world, vehicle, ...) → radar actor
    - Mount: x=2.5, y=0, z=0.5

capture.py:
  MultiSensorCapture handles synchronous mode
  Saves: images/{frame:06d}.png, pointcloud/{frame:06d}.pcd, labels/{frame:06d}.txt, metadata/{frame:06d}.json

population.py:
  filter_spawn_points(world, road_type) → list of spawn points
  spawn_background_traffic(world, client, resolved_scenario, road_type, traffic_density) → list of vehicles
  spawn_pedestrian_crowd(world, client, resolved_scenario, traffic_density) → (walkers, controllers)

====================================================================
F. EXISTING JOB LIFECYCLE
====================================================================

States: queued → running → completed | failed

DB Schema:
  users: id (PK), email (unique), password_hash, created_at
  projects: id (PK), user_id (FK), name, description, created_at
  jobs: id (PK, uuid), project_id (FK), status (str), progress (float),
        map (str, default "Town01"), sensors (JSON, default ["rgb"]),
        frames (int, default 500), export_format (str, default "kitti"),
        output_path (str, nullable), created_at (datetime)
  datasets: id (PK, uuid), job_id (FK), sensors (JSON), sensor_metadata (JSON),
            path (str), frame_count, rgb_count, lidar_count, annotation_count,
            export_format, created_at
  prompts: id (PK, uuid), user_id (FK), project_id (FK, nullable), text, created_at
  scenarios: id (PK, uuid), prompt_id (FK, scenario_json (JSON), llm_provider,
             job_id (FK, nullable), created_at
  revisions: id (PK, uuid), scenario_id (FK), version, refinement, scenario_json, created_at

Worker Lifecycle:
  poll_jobs() loops every 3s
    → finds first queued job
    → sets status=running, progress=0
    → calls generate_dataset_job(db, job)
      → connects to CARLA
      → loads map
      → applies weather
      → spawns ego + traffic + pedestrians + sensors
      → MultiSensorCapture.start_capture()
      → exports (kitti/coco/nuscenes)
      → writes Build 4 metadata files
      → ZIPs dataset
      → sets status=completed or failed
    → creates Dataset record
    → commits

====================================================================
G. EXISTING STORAGE LAYOUT
====================================================================

gwm-platform/storage/
  dataset_{job_id}.zip                    ← final deliverable
  dataset_{job_id}/                       ← temp during generation
    images/{frame:06d}.png
    pointcloud/{frame:06d}.pcd
    labels/{frame:06d}.txt
    metadata/{frame:06d}.json
    calibration/calib.json
    (optional) depth/, semantic/, instance/, optical_flow/,
               camera_front/, camera_left/, camera_right/, camera_rear/
    (optional) radar.csv
    (optional) kitti/, coco/, nuscenes/
    Build 4 files:
      resolved_scenario.json
      country_profile.json
      compiler_log.json
      metadata.json
      provenance.json
      capabilities.json
      quality.json
      difficulty.json

database/gwm.db (SQLite fallback)

====================================================================
H. EXISTING PROVENANCE SYSTEM
====================================================================

Build 4 provenance (app/country_profiles/compiler.py):
  - prompt_hash: SHA256(reality.model_dump())
  - scenario_hash: SHA256(resolved.model_dump())
  - compiler_version: "1.0.0"
  - country_profile: "{id}_v{version}"
  - carla_version: "0.9.16"
  - git_commit: "e82d31a5" (hardcoded)
  - seeds: {traffic_seed, spawn_seed, weather_seed}

Written to: provenance.json in dataset output

No existing geography provenance.

====================================================================
I. EXISTING TEST SUITE STRUCTURE
====================================================================

Standalone test scripts (run directly, no pytest):
  dataset-engine/tests/test_phase1.py
    - class mapping, KITTI mapping, intrinsics, extrinsics, bbox filters,
      full pipeline (5 frames synthetic), no-carla-import check

  Root-level:
    run_phase1_test.py through run_phase8_test.py
    run_remaining_verifications.py
    run_single_worker_job.py
    run_phase2_test_a.py, run_phase2_test_b.py
    run_phase3_test_a.py
    run_phase4_test_a.py
    run_phase5_test_a.py
    run_phase6_test_a.py
    run_phase7_test.py
    run_phase8_test.py

  Backend:
    gwm-platform/backend/test_e2e_country.py

No pytest.ini or pyproject.toml test config found.

====================================================================
J. GENUINE ARCHITECTURAL CONFLICTS FOUND
====================================================================

NONE.

- No `app/geography/` or `app/simulators/` directories exist.
- No name collisions with existing models.
- ScenarioConfig has `carla_map` field — Build 5 will add optional geographic
  fields without breaking existing flow.
- Job model has `map` column for CARLA town names — Build 5 will need to
  either extend this or add new columns for geographic locations.
- Worker's generate_dataset_job() reads scenario_json from ScenarioModel —
  Build 5 needs to inject geographic data before this point.

Safe to proceed without modifications to Build 4 locked behavior.

====================================================================
K. IMPLEMENTATION PLAN FOR PHASES 1+
====================================================================

Phase 1:  Create app/geography/models.py — Pydantic v2 models for all
          geographic entities. No CARLA imports.

Phase 2:  Create app/geography/geocoder.py — Geocoder interface with
          NominatimGeocoder implementation (timeout, retry, caching).

Phase 3:  Create app/geography/osm.py — OSMProvider interface with
          OverpassProvider implementation (rate limiting, attribution).

Phase 4:  Create storage/geography/cache/ — deterministic hash-keyed
          caching for OSM data.

Phase 5:  Create app/geography/graph.py — RoadGraph construction from
          OSM data (nodes, edges, intersection detection).

Phase 6:  Create app/geography/projection.py — WGS84 → local metric →
          CARLA coordinate projection with deterministic local origin.

Phase 7:  Create app/geography/opendrive.py — RoadGraph → OpenDRIVE
          .xodr compiler with documented fallbacks.

Phase 8:  Create app/geography/validator.py — OpenDRIVE XML validator
          checking IDs, references, geometry, NaN/Inf.

Phase 9:  Create app/geography/provenance.py — full pipeline provenance
          recording (geocoder, OSM, graph, OpenDRIVE, compiler versions).

Phase 10: Extend caching to cover full pipeline (graph, OpenDRIVE).

Phase 11: Add POST /geography/resolve and POST /geography/build API
          endpoints in app/api/geography.py.

Phase 12: Add frontend /geography page with location input, radius
          selector, progress display.

Phase 13: Live OSM integration test on Bengaluru region (500-1000m).

Phase 14: CARLA map loading via app/simulators/carla/adapter.py +
          map_loader.py — load .xodr into CARLA 0.9.16.

Phase 15: Spawn point validation on loaded custom map.

Phase 16: Minimal RGB capture (5-10 frames) on custom map.

Phase 17: Build 3 regression — non-geographic prompts still work.

Phase 18: Build 4 regression — country profiles still work.

Phase 19: Full end-to-end test: "Generate 500 meters of MG Road,
          Bengaluru, during a monsoon evening with moderate traffic."

Final: Merge to main, tag build-5-v1.0, push.
