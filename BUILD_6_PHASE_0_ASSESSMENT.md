# Build 6 — Phase 0 Implementation Assessment

## Repository State
- Branch: `build-6-procedural-world` (created from `main`)
- Tags: `build-3-v1.0`, `build-4-v1.0`, `build-5-v1.0` all present
- Working tree: clean (no uncommitted changes from Build 5)

## Architecture Isolation Verification

### Import checks
| Module | Imports `world_generation`? | Imports `carla`? |
|--------|---------------------------|-----------------|
| `app/country_profiles/` | NO | NO |
| `app/geography/` | NO | NO |
| `app/world_generation/` | N/A (does not exist yet) | NO (must enforce) |
| `app/simulators/carla/` | NO | YES (only allowed location) |
| `worker/` | NO | YES (via simulator.carla.*) |

### Verified: Zero illegal imports
- `grep -rn "import carla" app/geography/` → 0 matches
- `grep -rn "world_generation" app/country_profiles/` → 0 matches
- `grep -rn "world_generation" app/geography/` → 0 matches (only a comment about "procedural buildings" being out-of-scope)

## Key Existing Interfaces

### Build 4 (Country Profile Engine)
- `CountryProfile`: id, version, rules (drive_side, speed_limits, behavior), vehicle_mix, pedestrians, weather_presets
- `ResolvedScenario`: drive_side, weather, vehicles, pedestrians, speed_limits, behavior, difficulty_score, quality_score, warnings
- `RealityScenario`: country, weather, traffic, time_of_day, road_type, modifiers
- `registry.get_profile(country_id)` → `CountryProfile`
- `compiler.compile_scenario(reality)` → `(ResolvedScenario, provenance)`

### Build 5 (Geography Engine)
- `MapArtifact`: xodr_path, xodr_size_bytes, xodr_hash, validator_passed, carla_load_succeeded, carla_spawn_point_count, metadata
- `MapProvenance`: location_query, resolved_latitude/longitude, osm_file_path, road_graph_node/edge_count, xodr_hash, fallbacks, warnings, errors
- `RoadGraph`: nodes (RoadNode), edges (RoadEdge)
- `RoadNode`: node_id, coordinate (GeoCoordinate), node_type, roads
- `RoadEdge`: edge_id, from_node, to_node, road (Road), length_m, lane_count
- `Road`: osm_id, name, highway_type, lanes, maxspeed, oneway, surface, bridge, tunnel, geometry

### Build 3 (Prompt Engine)
- `ScenarioConfig`: country, weather, traffic_density, vehicles, pedestrians, sensors, frames, export_format, carla_map, etc.
- `parse_prompt(prompt)` → `ScenarioConfig`

### Database
- `jobs`: id, project_id, status, progress, map, sensors, frames, export_format, output_path, created_at
- `scenarios`: id, prompt_id, scenario_json, llm_provider, job_id
- `datasets`: id, job_id, sensors, path, frame_count, rgb_count, lidar_count, annotation_count, export_format

### Worker Pipeline
`poll_jobs()` → `generate_dataset_job(db, job)`:
1. Load scenario from DB
2. Compile Build 4 country profile
3. Connect to CARLA (version-checked)
4. Load map
5. Apply weather
6. Spawn ego vehicle
7. Spawn background traffic + pedestrians
8. Attach sensors
9. MultiSensorCapture (synchronous mode)
10. Export (KITTI/COCO/nuScenes)
11. Write Build 4 metadata files
12. ZIP dataset
13. Create Dataset record

### CARLA Adapter
- `connect()` → `(client, world)` with version check (0.9.16)
- `disconnect(client, actors)` → destroy all actors
- `load_simulation_map(client, map_name)` → world
- `spawn_ego_vehicle(world, filter)` → vehicle
- `attach_rgb_camera(world, vehicle)` → camera
- `attach_lidar(world, vehicle)` → lidar
- `MultiSensorCapture` handles synchronous capture

### Frontend
- React + TypeScript + Tailwind CSS
- React Router: `/`, `/projects`, `/generate`, `/generate-prompt`, `/jobs`, `/quality`, `/countries`
- TanStack Query for API calls
- Sidebar navigation

## Implementation Assessment

### Design Decisions
1. **WorldPlan-first architecture**: Build 6 generates a deterministic `WorldPlan` JSON before any CARLA interaction. The CARLA adapter only executes the plan.
2. **No CARLA imports in world_generation**: All world generation modules remain simulator-independent.
3. **Extend, don't replace**: Build 6 extends existing `MapArtifact` and `MapProvenance` rather than replacing them.
4. **Seeded RNG**: All randomization uses explicit seeds (world_seed, traffic_seed, pedestrian_seed, weather_seed, asset_seed, scenario_seed).
5. **Asset fallback chain**: Semantic assets resolve to CARLA blueprint candidates with explicit fallback metadata.

### Key Integration Points
- Build 6 planner takes `ResolvedScenario` (Build 4) + `MapArtifact` (Build 5) + `CountryProfile` (Build 4) as input
- Worker pipeline extends `generate_dataset_job()` to include Build 6 world generation between map load and sensor attachment
- Database: new `WorldPlan` and `WorldProvenance` tables linked to existing `jobs` table
- API: new `/world/*` endpoints added to FastAPI router
- Frontend: new `/world` page added to React Router

### Risks
1. CARLA 0.9.16 asset availability: Not all semantic assets (palm trees, specific building types) may have native CARLA blueprints. Fallback chain required.
2. OpenDRIVE loading gap (Build 5 known issue): Build 6 must support both Town maps and Build 5 artifacts without pretending the gap is solved.
3. Performance: World planning + asset resolution + placement must complete in reasonable time for API responsiveness.

### File Structure Plan
```
gwm-platform/backend/app/world_generation/
  __init__.py
  models.py              # WorldPlan, Building, Vegetation, Sign, TrafficLight, Vehicle, Pedestrian, Event, SensorConfig, WorldProvenance
  planner.py             # WorldPlanner: ResolvedScenario + MapArtifact + CountryProfile -> WorldPlan
  placement.py           # PlacementEngine: deterministic placement with collision/spacing rules
  rules.py               # Country/road-type specific placement rules
  randomization.py       # Seeded RNG for domain randomization
  provenance.py          # WorldProvenance generation with deterministic hashing
  resolver.py            # SemanticAssetResolver: semantic class -> CARLA blueprint candidates

gwm-platform/backend/app/sensor_realism/
  __init__.py
  models.py              # SensorConfig, RGBConfig, LiDARConfig, RadarConfig, DepthConfig
  calibration.py         # Camera calibration (K, R, T, extrinsics)

gwm-platform/backend/app/simulators/carla/
  carla_world_executor.py # Executes WorldPlan in CARLA (only place with carla imports for world gen)
  carla_assets.py         # CARLA asset registry and fallback mappings
  carla_spawn.py          # Spawn helpers for buildings, vegetation, vehicles, pedestrians
  carla_weather.py        # Weather application
  carla_traffic.py        # Traffic light and sign placement
  carla_sensors.py        # Sensor realism application

gwm-platform/backend/app/api/world.py  # POST /world/plan, /world/validate, /world/build, GET /world/{id}

gwm-platform/frontend/src/pages/WorldGeneration.tsx
gwm-platform/frontend/src/services/world.ts
```
