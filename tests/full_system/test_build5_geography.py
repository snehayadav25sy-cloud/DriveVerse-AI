"""
Full System Acceptance Test — Step 3: Build 5 Geography Engine
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import json
import hashlib
import requests
import pytest

API_BASE = "http://localhost:8000"


def test_build5_geography_engine():
    print("=" * 65)
    print("  STEP 3 — Build 5: Geography Engine")
    print("=" * 65)

    payload = {
        "location": "MG Road, Bengaluru, India",
        "radius_m": 500.0,
    }
    resp = requests.post(f"{API_BASE}/geography/build", json=payload, timeout=180)
    print(f"HTTP {resp.status_code}")
    assert resp.status_code == 200, f"Expected HTTP 200, got {resp.status_code}"
    data = resp.json()
    print(json.dumps(data, indent=2))
    
    status = data.get("status", "")
    assert status in ["complete", "completed_with_errors"], f"status={status}"
    
    stages = data.get("stages", {})
    
    resolve = stages.get("resolve", {})
    assert resolve.get("status") == "resolved", f"resolve={resolve}"
    assert resolve.get("latitude") is not None, f"resolve={resolve}"
    assert resolve.get("longitude") is not None, f"resolve={resolve}"
    assert "bengaluru" in str(resolve.get("city", "")).lower(), f"resolve={resolve}"
    
    osm = stages.get("osm", {})
    assert osm.get("status") == "downloaded", f"osm={osm}"
    assert osm.get("element_count", 0) > 0, f"osm={osm}"
    assert osm.get("road_count", 0) > 0, f"osm={osm}"
    
    graph = stages.get("graph", {})
    assert graph.get("status") == "built", f"graph={graph}"
    assert graph.get("node_count", 0) > 0, f"graph={graph}"
    assert graph.get("edge_count", 0) > 0, f"graph={graph}"
    assert graph.get("graph_hash") is not None, f"graph={graph}"
    
    projection = stages.get("projection", {})
    assert projection.get("status") == "projected", f"projection={projection}"
    
    opendrive = stages.get("opendrive", {})
    assert opendrive.get("status") == "compiled", f"opendrive={opendrive}"
    assert opendrive.get("size_bytes", 0) > 0, f"opendrive={opendrive}"
    assert opendrive.get("xodr_hash") is not None, f"opendrive={opendrive}"
    
    validate = stages.get("validate", {})
    assert validate.get("status") in ["valid", "invalid"], f"validate={validate}"
    assert validate.get("statistics") is not None, f"validate={validate}"
    
    map_artifact = data.get("map_artifact")
    assert map_artifact is not None, "map_artifact missing"
    assert map_artifact.get("xodr_path") is not None, f"map_artifact={map_artifact}"
    assert map_artifact.get("xodr_hash") is not None, f"map_artifact={map_artifact}"
    
    provenance = data.get("provenance")
    assert provenance is not None, "provenance missing"
    assert provenance.get("provenance_hash") is not None, f"provenance={provenance}"
    
    print("\n" + "=" * 65)
    print("  BUILD 5 RESULT: PASS")
    print("=" * 65)
