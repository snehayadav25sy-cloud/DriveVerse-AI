"""
Unit tests for the new deck.gl GeoJSON endpoint: POST /geography/graph
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gwm-platform", "backend")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_geography_graph_endpoint_missing_payload():
    resp = client.post("/geography/graph", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    assert "Provide 'location'" in data["error"]


def test_geography_graph_endpoint_with_coordinates():
    # MG Road coordinates
    resp = client.post("/geography/graph", json={
        "latitude": 12.9755,
        "longitude": 77.6068,
        "radius_m": 300.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["complete", "failed"]
    if data["status"] == "complete":
        assert data["center_lat"] == 12.9755
        assert data["center_lon"] == 77.6068
        assert "geojson" in data
        assert data["geojson"]["type"] == "FeatureCollection"
        assert isinstance(data["geojson"]["features"], list)
        assert data["node_count"] >= 0
        assert data["edge_count"] >= 0
