"""
DriveVerse AI — Full Pipeline Validation via Real API (Standard Library urllib)
Steps 3-5: Auth → Submit Job → Poll to completion
"""
import urllib.request
import urllib.parse
import time
import json
import sqlite3

BASE = "http://localhost:8000"
DB_PATH = r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\database\gwm.db"

def http_post(url, data_dict, headers_dict=None):
    if headers_dict is None:
        headers_dict = {}
    headers_dict["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(data_dict).encode("utf-8"), headers=headers_dict, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, body

def http_get(url, headers_dict=None):
    if headers_dict is None:
        headers_dict = {}
    req = urllib.request.Request(url, headers=headers_dict, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            body = json.loads(body)
        except Exception:
            pass
        return e.code, body

print("=" * 60)
print("STEP 3: Project confirmation / creation")
print("=" * 60)

# Register (will fail if already exists)
reg_status, reg_body = http_post(f"{BASE}/auth/register", {"email": "test@driveverse.ai", "password": "test1234"})
print(f"Register response: {reg_status} {json.dumps(reg_body)}")

# Login
login_status, login_body = http_post(f"{BASE}/auth/login", {"email": "test@driveverse.ai", "password": "test1234"})
print(f"Login response: {login_status} {json.dumps(login_body)}")
token = login_body["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# List existing projects
projs_status, projs_body = http_get(f"{BASE}/projects", headers)
print(f"Projects list: {projs_status} {json.dumps(projs_body)}")

project_id = None
if projs_status == 200 and projs_body:
    project_id = projs_body[0]["id"]
    print(f"Using existing project: {project_id}")
else:
    cp_status, cp_body = http_post(f"{BASE}/projects", {"name": "Final Validation"}, headers)
    print(f"Create project: {cp_status} {json.dumps(cp_body)}")
    project_id = cp_body["id"]

# Step 3.2: Direct DB verification
print("\n--- Step 3.2: Direct DB verification ---")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,))
row = cur.fetchone()
print(f"DB project record: {row}")

# ── Step 4: Submit the real job ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Submit real dataset generation job")
print("=" * 60)

job_payload = {
    "project_id": project_id,
    "map": "Town01",
    "sensors": ["rgb", "lidar"],
    "frames": 25,
    "export_format": "kitti"
}
print(f"Submitting job with payload: {json.dumps(job_payload, indent=2)}")

submit_time = time.time()
resp_status, resp_body = http_post(f"{BASE}/jobs", job_payload, headers)
print(f"\n--- Step 4.2: Raw JSON response ---")
print(f"Status: {resp_status}")
print(f"Body: {json.dumps(resp_body, indent=2)}")

job_id = resp_body["id"]
print(f"\nAssigned job UUID: {job_id}")

# Step 4.3: Direct DB verification
print("\n--- Step 4.3: Direct DB verification ---")
cur.execute("SELECT id, project_id, status, map, sensors, frames, export_format, created_at FROM jobs WHERE id = ?", (job_id,))
row = cur.fetchone()
print(f"DB job record: {row}")

# ── Step 5: Poll job lifecycle ───────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Poll job status until completion or failure")
print("=" * 60)

poll_count = 0
while True:
    poll_count += 1
    poll_status, pdata = http_get(f"{BASE}/jobs/{job_id}", headers)
    elapsed = time.time() - submit_time
    print(f"Poll #{poll_count} [{elapsed:.1f}s]: status={pdata['status']}, progress={pdata['progress']}")
    
    if pdata["status"] in ("completed", "failed"):
        break
    
    time.sleep(5)

completion_time = time.time() - submit_time
print(f"\n--- Step 5.2: Total wall-clock time: {completion_time:.1f}s ---")

if pdata["status"] == "failed":
    print(f"\n*** PIPELINE FAILED AT STEP 5 ***")
    cur.execute("SELECT id, status, progress, output_path FROM jobs WHERE id = ?", (job_id,))
    fail_row = cur.fetchone()
    print(f"Failed job DB record: {fail_row}")
    conn.close()
    exit(1)

print(f"\nJob {job_id} completed successfully in {completion_time:.1f}s")

# Step 5: Final DB record
print("\n--- Step 5: Final DB job record ---")
cur.execute("SELECT id, status, progress, created_at, completed_at FROM jobs WHERE id = ?", (job_id,))
row = cur.fetchone()
print(f"Final DB record: {row}")

conn.close()
print(f"\n=== JOB_ID FOR REMAINING STEPS: {job_id} ===")
