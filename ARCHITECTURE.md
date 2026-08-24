# DriveVerse AI — System Architecture

This document details the software architecture, modular boundaries, data flows, and build progression of the DriveVerse AI platform.

---

## 1. Project Directory Layout

```
driveverseAI/
├── archive/                   # Historical reference diagnostic & validation scripts
├── database/                  # Canonical database directory containing gwm.db (SQLite)
├── gwm-platform/
│   ├── backend/               # FastAPI Server Application
│   │   ├── app/
│   │   │   ├── api/           # Endpoint controllers (jobs, analytics, projects, profiles)
│   │   │   ├── country_profiles/ # Registry & parameter validation for profiles (India/Mauritius)
│   │   │   ├── database/      # SQLite session config & models
│   │   │   ├── geography/     # OSM provider, geocoder, road validator, and OpenDRIVE compiler
│   │   │   ├── simulators/    # CARLA simulator clients and adapters
│   │   │   ├── world_generation/ # Scenario & world planner
│   │   │   └── scenario_execution/ # Event scheduling logic
│   ├── frontend/              # React + Vite Web Application
│   └── worker/                # Offline CARLA simulation dataset generation worker
│       └── simulator/
│           └── carla/         # Synchronous multi-sensor recording logic
├── tests/                     # Automated unit and integration test suite
│   ├── full_system/           # End-to-end integration tests (Build 1 through Build 7 verification)
└── requirements-carla.txt     # Python client pinned dependencies (Python 3.10.11)
```

---

## 2. Architectural Boundaries & Adapter Rules

### CARLA Import Isolation Rule
* **Rule:** Direct imports of the `carla` library (`import carla`) are strictly forbidden inside backend modules (`app/geography/`, `app/api/`, etc.) or non-simulation code.
* **Implementation:** The `carla` module must only be imported inside `gwm-platform/backend/app/simulators/carla/` (adapters) and `gwm-platform/worker/simulator/carla/` (worker capture loop). This ensures that geographic mapping and scenario planning logic can execute and be verified headlessly without importing CARLA.

### Mock Fallback Rule
* **Rule:** If the CARLA simulator server is offline, the backend must raise a clean connection error or use structured fallback objects — never silently emit fake mock sensor frames when a real simulation run was requested.

---

## 3. Core Data Flow & Generation Pipeline

```
[User Web UI] -> [FastAPI backend/app/api] -> [SQLite gwm.db]
                                                     |
                                            (Spawns offline job)
                                                     |
                                                     v
                                          [gwm-platform/worker]
                                                     |
                                (Launches CARLA client connection)
                                                     |
                                                     v
                                      [CARLA 0.9.16 Simulator Server]
                                                     |
                                          (Attach sensors & replay)
                                                     |
                                                     v
                                       [RGB Video & LiDAR Frame Output]
```

1. **Parameter Setup:** The user configures scenario parameters, geographic profiles, and seeds on the React Frontend.
2. **Scenario Design:** Backend planner converts configuration inputs into a deterministic `WorldPlan` and `EventSchedule`.
3. **Execution:** The worker connects to the CARLA server, loads the OpenDRIVE map, attaches camera/LiDAR sensors, triggers timed scenario events, and streams frames synchronously to disk.
4. **Validation:** Bounding boxes are computed from the 3D actor coordinates and projected into 2D labels.
