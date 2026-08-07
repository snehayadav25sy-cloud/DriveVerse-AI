"""
Phase 9 tests — Geography provenance

Run:
    python gwm-platform/backend/app/geography/test_phase9.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.geography.provenance import compute_map_provenance, provenance_hash

PASS = "PASS"
FAIL = "FAIL"
results = []

def check(condition: bool, description: str):
    status = PASS if condition else FAIL
    results.append((status, description))
    print(f"  [{status}]  {description}")
    if not condition:
        raise AssertionError(f"CHECK FAILED: {description}")


def test_9_1_generate_provenance():
    """9.1 Generate provenance for Phase 7 map and paste raw JSON."""
    print("\n[9.1] Generate provenance JSON")
    prov = compute_map_provenance(
        location_query="MG Road, Bengaluru",
        radius_m=500.0,
        geocoder_provider="nominatim",
        osm_provider="overpass",
        resolved_latitude=12.9755264,
        resolved_longitude=77.6067902,
        resolved_country="India",
        resolved_city="Bengaluru",
        bbox={"south": 12.97, "north": 12.98, "west": 77.59, "east": 77.60},
        osm_file_path="/tmp/geography/cache/abc/source.json",
        osm_file_size_bytes=672545,
        osm_timestamp="2026-08-07T16:58:11Z",
        osm_source_hash="sha256:deadbeef",
        road_graph_node_count=3005,
        road_graph_edge_count=659,
        road_graph_hash="sha256:1234567890abcdef",
        xodr_hash="sha256:fedcba0987654321",
        compiler_version="1.0.0",
        schema_version="1.0.0",
        country_profile_version="india_v1.0.0",
        carla_version="0.9.16",
        random_seed=42,
        fallbacks=["12 roads had no maxspeed tag, defaulted to 50.0 km/h"],
        warnings=["High number of missing maxspeed tags"],
        errors=[],
    )
    raw = prov.model_dump_json(indent=2)
    print(raw)
    check(prov.location_query == "MG Road, Bengaluru", "location_query populated")
    check(prov.radius_m == 500.0, "radius_m populated")
    check(prov.geocoder_provider == "nominatim", "geocoder_provider populated")
    check(prov.osm_provider == "overpass", "osm_provider populated")
    check(prov.resolved_latitude == 12.9755264, "resolved_latitude populated")
    check(prov.resolved_longitude == 77.6067902, "resolved_longitude populated")
    check(prov.resolved_country == "India", "resolved_country populated")
    check(prov.resolved_city == "Bengaluru", "resolved_city populated")
    check(prov.bbox is not None, "bbox populated")
    check(prov.osm_file_path is not None, "osm_file_path populated")
    check(prov.osm_file_size_bytes == 672545, "osm_file_size_bytes populated")
    check(prov.osm_timestamp is not None, "osm_timestamp populated")
    check(prov.osm_source_hash is not None, "osm_source_hash populated")
    check(prov.road_graph_node_count == 3005, "road_graph_node_count populated")
    check(prov.road_graph_edge_count == 659, "road_graph_edge_count populated")
    check(prov.road_graph_hash is not None, "road_graph_hash populated")
    check(prov.xodr_hash is not None, "xodr_hash populated")
    check(prov.compiler_version == "1.0.0", "compiler_version populated")
    check(prov.schema_version == "1.0.0", "schema_version populated")
    check(prov.country_profile_version == "india_v1.0.0", "country_profile_version populated")
    check(prov.carla_version == "0.9.16", "carla_version populated")
    check(prov.git_commit != "unknown", "git_commit populated")
    check(prov.random_seed == 42, "random_seed populated")
    check(len(prov.fallbacks) > 0, "fallbacks populated")
    check(len(prov.warnings) > 0, "warnings populated")
    check(prov.errors == [], "errors empty (no errors)")


def test_9_2_reproducibility():
    """9.2 Re-run same pipeline — matching hashes."""
    print("\n[9.2] Reproducibility check — two runs produce matching hashes")

    def make_prov():
        return compute_map_provenance(
            location_query="MG Road, Bengaluru",
            radius_m=500.0,
            geocoder_provider="nominatim",
            osm_provider="overpass",
            resolved_latitude=12.9755264,
            resolved_longitude=77.6067902,
            resolved_country="India",
            resolved_city="Bengaluru",
            osm_file_size_bytes=672545,
            road_graph_node_count=3005,
            road_graph_edge_count=659,
            road_graph_hash="sha256:1234567890abcdef",
            xodr_hash="sha256:fedcba0987654321",
            random_seed=42,
        )

    prov1 = make_prov()
    prov2 = make_prov()
    hash1 = provenance_hash(prov1)
    hash2 = provenance_hash(prov2)

    print(f"    Run 1 hash: {hash1}")
    print(f"    Run 2 hash: {hash2}")
    check(hash1 == hash2, "Provenance hashes are identical across two runs")


if __name__ == "__main__":
    print("=" * 65)
    print("  Phase 9 - Geography Provenance Tests")
    print("=" * 65)

    try:
        test_9_1_generate_provenance()
        test_9_2_reproducibility()
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
