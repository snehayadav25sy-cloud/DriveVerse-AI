"""
Phase 19 tests — Final end-to-end test

Prompt: "Generate 500 meters of MG Road, Bengaluru, during a monsoon evening with moderate traffic."

Full chain:
  Build 3: Prompt -> ScenarioConfig
  Build 4: Country Profile (India) -> ResolvedScenario
  Build 5: Geography Engine -> OSM -> RoadGraph -> OpenDRIVE -> Validator
  CARLA:   Connect -> Load map -> Spawn vehicle -> Capture RGB frames

KNOWN LIMITATION: CARLA 0.9.16 does not support dynamic OpenDRIVE loading
from Python. The .xodr is XML-valid (Phase 8) but CARLA load_world() fails
with "Map 'phase19_map' not found". This is a REAL, documented gap.

Run:
    python gwm-platform/backend/app/geography/test_phase19.py
"""

import sys
import os
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import requests

from app.geography.geocoder import NominatimGeocoder
from app.geography.osm import OverpassProvider
from app.geography.graph import build_graph_from_osm, graph_hash
from app.geography.projection import project_graph
from app.geography.opendrive import OpenDriveCompiler
from app.geography.validator import OpenDriveValidator
from app.geography.provenance import compute_map_provenance, provenance_hash
from app.simulators.carla.adapter import connect, disconnect, check_carla_available, CarlaAdapterError, make_weather
from app.simulators.carla.camera import attach_rgb_camera

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


BASE_URL = "http://127.0.0.1:8000"


def _get_token() -> str:
    email = "test-phase19@example.com"
    password = "testpass123"
    requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password}, timeout=10)
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=10)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")


def test_19_end_to_end():
    """19: Full end-to-end chain."""
    print("\n[19] Final end-to-end test")
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Prompt -> ScenarioConfig (Build 3)
    print("\n  --- Step 1: Build 3 Prompt Parsing ---")
    prompt = "Generate 500 meters of MG Road, Bengaluru, during a monsoon evening with moderate traffic."
    payload = {"prompt": prompt, "project_id": "test-project"}
    resp = requests.post(f"{BASE_URL}/prompt/parse", json=payload, headers=headers, timeout=30)
    check(resp.status_code == 200, f"Prompt parse HTTP 200 ({resp.status_code})")
    scenario = resp.json()
    print(f"    country: {scenario.get('country')}")
    print(f"    weather: {scenario.get('weather')}")
    print(f"    carla_map: {scenario.get('carla_map')}")

    # Step 2: Country Profile (Build 4)
    print("\n  --- Step 2: Build 4 Country Profile ---")
    country_resp = requests.get(f"{BASE_URL}/countries/india", headers=headers, timeout=30)
    check(country_resp.status_code == 200, "India profile loads")
    profile = country_resp.json()
    drive_side = profile.get("rules", {}).get("drive_side")
    print(f"    drive_side: {drive_side}")
    check(drive_side == "left", "India drive_side = left")

    # Step 3: Geography Engine (Build 5)
    print("\n  --- Step 3: Build 5 Geography Engine ---")
    geocoder = NominatimGeocoder()
    resolution = geocoder.geocode("MG Road, Bengaluru")
    check(resolution is not None, "Geocode MG Road, Bengaluru")
    if resolution is None:
        return
    lat = resolution.latitude
    lon = resolution.longitude
    print(f"    location: lat={lat}, lon={lon}")
    check(resolution.country == "India", "Resolved country = India")

    # OSM download
    osm_provider = OverpassProvider()
    raw = osm_provider.download_radius(lat, lon, 500.0)
    check(raw is not None, "OSM download succeeded")
    roads = osm_provider.fetch_roads()
    intersections = osm_provider.fetch_intersections()
    print(f"    OSM elements: {len(raw.get('elements', []))}")
    print(f"    roads: {len(roads)}, intersections: {len(intersections)}")

    # Graph
    graph = build_graph_from_osm(roads, intersections)
    ghash = graph_hash(graph)
    print(f"    graph: nodes={graph.node_count()}, edges={graph.edge_count()}")
    check(graph.node_count() > 0, "Graph has nodes")
    check(graph.edge_count() > 0, "Graph has edges")

    # Projection
    projected = project_graph(graph, lat, lon)

    # OpenDRIVE
    compiler = OpenDriveCompiler(projected)
    xodr_path = os.path.join(tempfile.mkdtemp(), "phase19_map.xodr")
    compile_meta = compiler.compile(xodr_path)
    print(f"    .xodr path: {xodr_path}")
    print(f"    .xodr size: {compile_meta['xodr_size_bytes']} bytes")
    check(os.path.exists(xodr_path), ".xodr file exists")
    check(compile_meta["xodr_size_bytes"] > 0, ".xodr non-empty")

    # Validate
    validator = OpenDriveValidator()
    vresult = validator.validate(xodr_path)
    print(f"    OpenDRIVE valid: {vresult['valid']}")
    check(vresult["valid"] is True, "OpenDRIVE validates")

    # Provenance
    prov = compute_map_provenance(
        location_query="MG Road, Bengaluru",
        radius_m=500.0,
        geocoder_provider="nominatim",
        osm_provider="overpass",
        resolved_latitude=lat,
        resolved_longitude=lon,
        resolved_country="India",
        resolved_city="Bengaluru",
        osm_file_size_bytes=len(str(raw).encode("utf-8")),
        road_graph_node_count=graph.node_count(),
        road_graph_edge_count=graph.edge_count(),
        road_graph_hash=ghash,
        xodr_hash=compile_meta["xodr_hash"],
        fallbacks=compile_meta.get("fallbacks", []),
        warnings=vresult["warnings"],
        errors=vresult["errors"],
    )
    phash = provenance_hash(prov)
    print(f"    provenance hash: {phash[:16]}...")

    # Step 4: CARLA
    print("\n  --- Step 4: CARLA Map Loading ---")
    available, err = check_carla_available()
    check(available is True, f"CARLA available: {available}")

    client = None
    actors = []
    carla_result = {}
    try:
        client, world = connect()
        carla_result["world_name"] = world.get_map().name
        carla_result["spawn_point_count"] = len(world.get_map().get_spawn_points())

        # Attempt to load custom map
        from app.simulators.carla.map_loader import load_opendrive_map
        load_result = load_opendrive_map(xodr_path)
        carla_result["load_success"] = load_result["success"]
        carla_result["load_error"] = load_result["error"]
        carla_result["load_detail"] = load_result["detail"]

        # Spawn vehicle and capture on current map (since custom map didn't load)
        bp_lib = world.get_blueprint_library()
        vehicle_bp = bp_lib.find("vehicle.tesla.model3")
        if vehicle_bp is None:
            vehicle_bp = bp_lib.find("vehicle.*")
        sp = world.get_map().get_spawn_points()[0]
        vehicle = world.spawn_actor(vehicle_bp, sp)
        actors.append(vehicle)
        print(f"    Spawned vehicle: {vehicle.type_id}")

        # Apply monsoon weather (Build 4)
        weather = make_weather(
            cloudiness=100.0,
            precipitation=95.0,
            precipitation_deposits=90.0,
            wind_intensity=65.0,
            fog_density=25.0,
            fog_distance=25.0,
            sun_altitude_angle=15.0,
            wetness=100.0,
        )
        world.set_weather(weather)
        print(f"    Applied monsoon weather")

        # RGB camera using adapter wrapper
        camera = attach_rgb_camera(world, vehicle)
        actors.append(camera)

        settings = world.get_settings()
        settings.synchronous_mode = True
        settings.fixed_delta_seconds = 0.1
        world.apply_settings(settings)
        world.tick()

        tmpdir = tempfile.mkdtemp(prefix="phase19_capture_")
        frame_paths = []

        def on_image(image):
            idx = len(frame_paths)
            path = os.path.join(tmpdir, f"{idx:06d}.png")
            image.save_to_disk(path)
            frame_paths.append(path)

        camera.listen(on_image)
        for _ in range(20):
            world.tick()
            time.sleep(0.05)
        camera.stop()
        settings.synchronous_mode = False
        world.apply_settings(settings)

        print(f"    Captured {len(frame_paths)} frames to {tmpdir}")
        valid = sum(1 for p in frame_paths if os.path.exists(p) and os.path.getsize(p) > 1000)
        check(len(frame_paths) >= 2, f"At least 2 frames captured ({len(frame_paths)})")
        check(valid >= 2, f"At least 2 valid frames ({valid})")

    except CarlaAdapterError as e:
        print(f"    CARLA error: {e}")
        check(False, f"CARLA failed: {e}")
    except Exception as e:
        print(f"    Unexpected error: {type(e).__name__}: {e}")
        check(False, f"Unexpected: {e}")
    finally:
        disconnect(client, actors)

    # Final summary
    print("\n  === FINAL SUMMARY ===")
    print(f"    location: lat={lat}, lon={lon} (MG Road, Bengaluru)")
    print(f"    country: India (drive_side=left)")
    print(f"    OSM source: {len(raw.get('elements', []))} elements")
    print(f"    road graph: {graph.node_count()} nodes, {graph.edge_count()} edges")
    print(f"    .xodr: {xodr_path} ({compile_meta['xodr_size_bytes']} bytes)")
    print(f"    OpenDRIVE valid: {vresult['valid']}")
    print(f"    CARLA load: {carla_result.get('load_success', False)}")
    print(f"    CARLA error: {carla_result.get('load_error', 'N/A')}")
    print(f"    spawn points: {carla_result.get('spawn_point_count', 'N/A')}")
    print(f"    frames captured: {valid if 'valid' in dir() else 'N/A'}")
    print(f"    provenance hash: {phash[:16]}...")
    print(f"    GAP: OpenDRIVE valid={vresult['valid']} but CARLA loaded={carla_result.get('load_success', False)}")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 19 - Final End-to-End Test")
    print("=" * 65)

    try:
        test_19_end_to_end()
    except AssertionError:
        pass
    finally:
        passed = sum(1 for s, _ in results if s == PASS)
        failed = sum(1 for s, _ in results if s == FAIL)
        print("\n" + "=" * 65)
        print(f"  Results: {passed} passed, {failed} failed")
        print("=" * 65)
        if failed > 0:
            sys.exit(1)
