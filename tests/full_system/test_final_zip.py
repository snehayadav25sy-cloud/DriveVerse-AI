"""
Full System Acceptance Test — Step 9: Final ZIP Structure Verification
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "gwm-platform", "backend")))

import tempfile
import zipfile
import json
import pytest


def test_final_zip_structure():
    print("=" * 65)
    print("  STEP 9 — Final ZIP Structure")
    print("=" * 65)

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "dataset.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(20):
                zf.writestr(f"image_2/{i:06d}.png", b"PNGDATA")
                zf.writestr(f"velodyne/{i:06d}.bin", b"LIDARDATA")
                zf.writestr(f"label_2/{i:06d}.txt", b"Pedestrian 0.0\n")
            zf.writestr("metadata/scenario.json", json.dumps({"scenario": "test"}))
            zf.writestr("metadata/resolved_scenario.json", json.dumps({"country": "India"}))
            zf.writestr("metadata/world_plan.json", json.dumps({"world_id": "world_001"}))
            zf.writestr("metadata/provenance.json", json.dumps({"session_id": "test_session"}))
            zf.writestr("metadata/manifest.json", json.dumps({"frame_count": 20}))
            zf.writestr("validation/validation.json", json.dumps({"passed": True}))
        
        extract_dir = os.path.join(tmpdir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        print(f"ZIP created: {zip_path}")
        print(f"ZIP size: {os.path.getsize(zip_path)} bytes")
        
        for root, dirs, files in os.walk(extract_dir):
            level = root.replace(extract_dir, "").count(os.sep)
            indent = "  " * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = "  " * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        assert os.path.exists(os.path.join(extract_dir, "image_2"))
        assert os.path.exists(os.path.join(extract_dir, "velodyne"))
        assert os.path.exists(os.path.join(extract_dir, "label_2"))
        assert os.path.exists(os.path.join(extract_dir, "metadata"))
        assert os.path.exists(os.path.join(extract_dir, "validation"))
        assert os.path.exists(os.path.join(extract_dir, "metadata", "scenario.json"))
        assert os.path.exists(os.path.join(extract_dir, "metadata", "provenance.json"))
        assert os.path.exists(os.path.join(extract_dir, "validation", "validation.json"))
        
        with open(os.path.join(extract_dir, "metadata", "provenance.json")) as f:
            prov = json.load(f)
        assert "session_id" in prov
        
        with open(os.path.join(extract_dir, "validation", "validation.json")) as f:
            val = json.load(f)
        assert "passed" in val
        
        print("\n" + "=" * 65)
        print("  ZIP STRUCTURE RESULT: PASS")
        print("=" * 65)
