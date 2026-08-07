import sys
import os
import json
import time
import uuid
import zipfile

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.database.database import SessionLocal
from app.models.job import Job
from app.models.prompt import Prompt as PromptModel, Scenario as ScenarioModel, Revision
from app.schemas.scenario import ScenarioConfig
from app.country_profiles import registry, compiler
from app.country_profiles.models import RealityScenario

def run_test():
    print("=== Phase 10: E2E Scenario Expansion & Capture Test ===")
    
    # 1. Simulate API submit of prompt
    prompt = "Generate a rainy highway with heavy traffic in India, Town01, 10 frames"
    print(f"User Prompt: '{prompt}'")
    
    db = SessionLocal()
    project_id = "test-project-build4"
    
    # Extract mock project or use default first project
    from app.models.project import Project
    proj = db.query(Project).first()
    if not proj:
        # Create a temp project
        proj = Project(id=project_id, name="Test Project", description="Test Build 4")
        db.add(proj)
        db.commit()
    project_id = proj.id
    
    # Run parsing pipeline
    from app.services.prompt_parser import parse_prompt
    cfg = parse_prompt(prompt)
    print(f"Parsed Reality attributes: country={cfg.country}, weather={cfg.weather}, traffic={cfg.traffic_density}, map={cfg.carla_map}")
    
    # Save prompt & scenario config to database
    prompt_row = PromptModel(
        id=str(uuid.uuid4()),
        user_id="test-user-id", # dummy user mapping or find first user
        project_id=project_id,
        text=prompt
    )
    # Find first user
    from app.models.user import User
    usr = db.query(User).first()
    if usr:
        prompt_row.user_id = usr.id
        
    db.add(prompt_row)
    
    scenario_row = ScenarioModel(
        id=str(uuid.uuid4()),
        prompt_id=prompt_row.id,
        scenario_json=cfg.model_dump(),
        llm_provider="regex"
    )
    db.add(scenario_row)
    db.flush()
    
    # Submit job (10 frames for fast testing)
    job = Job(
        id=str(uuid.uuid4()),
        project_id=project_id,
        map=cfg.carla_map or "Town01",
        sensors=["rgb", "lidar"],
        frames=10,
        export_format="kitti",
        status="queued"
    )
    db.add(job)
    scenario_row.job_id = job.id
    db.commit()
    
    print(f"Submitted Job ID: {job.id} (queued)")
    
    # 2. Wait for worker to pick up and process
    print("Waiting for worker to process job (may take up to 20 seconds)...")
    timeout = 60
    start_time = time.time()
    completed = False
    
    while time.time() - start_time < timeout:
        db.refresh(job)
        print(f"  Job Status: {job.status} | Progress: {job.progress}%")
        if job.status in ["completed", "failed"]:
            if job.status == "completed":
                completed = True
            break
        time.sleep(4)
        
    if not completed:
        print(f"ERROR: Job did not complete. Status: {job.status}. Error: {job.error if hasattr(job, 'error') else 'None'}")
        db.close()
        sys.exit(1)
        
    print(f"SUCCESS: Job completed. Output ZIP path: {job.output_path}")
    
    # 3. Verify ZIP contents
    if not os.path.exists(job.output_path):
        print(f"ERROR: ZIP file not found at {job.output_path}")
        db.close()
        sys.exit(1)
        
    with zipfile.ZipFile(job.output_path, 'r') as zf:
        namelist = zf.namelist()
        print(f"ZIP File count: {len(namelist)} items")
        
        # Verify required Build 4 outputs are present
        required_files = [
            "resolved_scenario.json",
            "country_profile.json",
            "compiler_log.json",
            "metadata.json",
            "provenance.json",
            "capabilities.json",
            "quality.json",
            "difficulty.json"
        ]
        
        missing = []
        for r_file in required_files:
            if r_file not in namelist:
                missing.append(r_file)
                
        if missing:
            print(f"ERROR: Missing output files in ZIP: {missing}")
            db.close()
            sys.exit(1)
            
        print("Required Build 4 output files are verified inside ZIP: PASS")
        
        # Read difficulty and metadata
        with zf.open("difficulty.json") as f:
            diff_data = json.load(f)
            print(f"Difficulty Score: {diff_data.get('overall_difficulty_score')} factors: {diff_data.get('factors')}")
            
        with zf.open("resolved_scenario.json") as f:
            res_data = json.load(f)
            print(f"Resolved Scenario drive side: {res_data.get('drive_side')} (Expected: left for India)")
            print(f"Resolved Scenario warnings: {res_data.get('warnings')}")
            
    db.close()
    print("=== E2E Integration Test: ALL PASSED ===")

if __name__ == "__main__":
    run_test()
