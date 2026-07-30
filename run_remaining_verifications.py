"""
DriveVerse AI — Remaining Verifications (Steps 6 - 13)
For Job ID: 702874b3-b4a8-400d-ab33-a226f766d82a
"""
import sqlite3, os, zipfile, json

JOB_ID = "702874b3-b4a8-400d-ab33-a226f766d82a"
DB_PATH = r"C:\Users\sneha_nqarngz\Downloads\driveverseAI\database\gwm.db"
ZIP_PATH = rf"C:\Users\sneha_nqarngz\Downloads\driveverseAI\gwm-platform\storage\dataset_{JOB_ID}.zip"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print("=" * 60)
print("STEP 6: Storage artifact check")
print("=" * 60)
print(f"ZIP path: {ZIP_PATH}")
print(f"Exists: {os.path.exists(ZIP_PATH)}")
if os.path.exists(ZIP_PATH):
    size = os.path.getsize(ZIP_PATH)
    print(f"Size: {size} bytes ({size / (1024*1024):.2f} MB)")

print("\n" + "=" * 60)
print("STEP 7: ZIP contents inventory")
print("=" * 60)
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    namelist = zf.namelist()
    print(f"Total files in ZIP: {len(namelist)}")
    png_files = [f for f in namelist if f.endswith(".png")]
    pcd_files = [f for f in namelist if f.endswith(".pcd")]
    txt_files = [f for f in namelist if f.endswith(".txt")]
    json_files = [f for f in namelist if f.endswith(".json")]
    
    print(f"PNG count: {len(png_files)}")
    print(f"PCD count: {len(pcd_files)}")
    print(f"TXT count: {len(txt_files)}")
    print(f"JSON count: {len(json_files)}")
    
    print("\nFile tree in ZIP:")
    for name in namelist[:30]:
        print(f"  {name}")
    if len(namelist) > 30:
        print(f"  ... and {len(namelist) - 30} more files")

print("\n" + "=" * 60)
print("STEP 8: Metadata validation")
print("=" * 60)
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    meta_bytes = zf.read("metadata.json")
    meta = json.loads(meta_bytes.decode('utf-8'))
    print("metadata.json content:")
    print(json.dumps(meta, indent=2))

print("\n" + "=" * 60)
print("STEP 9: KITTI export structure verification")
print("=" * 60)
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    kitti_files = [f for f in namelist if f.startswith("kitti/")]
    print(f"Total KITTI files: {len(kitti_files)}")
    kitti_images = [f for f in kitti_files if "image_2/" in f]
    kitti_velodyne = [f for f in kitti_files if "velodyne/" in f]
    kitti_labels = [f for f in kitti_files if "label_2/" in f]
    kitti_calib = [f for f in kitti_files if "calib/" in f]
    
    print(f"kitti/image_2 files: {len(kitti_images)}")
    print(f"kitti/velodyne files: {len(kitti_velodyne)}")
    print(f"kitti/label_2 files: {len(kitti_labels)}")
    print(f"kitti/calib files: {len(kitti_calib)}")
    
    # Read sample calibration file
    sample_calib = kitti_calib[0] if kitti_calib else None
    if sample_calib:
        print(f"\nSample KITTI calibration file ({sample_calib}):")
        print(zf.read(sample_calib).decode('utf-8'))
        
    # Read sample label file
    sample_label = kitti_labels[0] if kitti_labels else None
    if sample_label:
        print(f"\nSample KITTI label file ({sample_label}):")
        print(zf.read(sample_label).decode('utf-8')[:300])

print("\n" + "=" * 60)
print("STEP 10: Database consistency verification")
print("=" * 60)
cur.execute("SELECT * FROM jobs WHERE id = ?", (JOB_ID,))
job_row = cur.fetchone()
print(f"jobs record: {job_row}")

cur.execute("SELECT * FROM datasets WHERE job_id = ?", (JOB_ID,))
ds_row = cur.fetchone()
print(f"datasets record: {ds_row}")

print("\n" + "=" * 60)
print("STEP 11: GET /datasets API endpoint test")
print("=" * 60)
import urllib.request
req = urllib.request.Request('http://localhost:8000/auth/login', data=json.dumps({'email':'test@driveverse.ai','password':'test1234'}).encode(), headers={'Content-Type':'application/json'}, method='POST')
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']
headers = {'Authorization': f'Bearer {token}'}

req = urllib.request.Request('http://localhost:8000/datasets', headers=headers)
resp = urllib.request.urlopen(req)
print(f"GET /datasets status: {resp.status}")
datasets_list = json.loads(resp.read().decode('utf-8'))
print(f"GET /datasets response count: {len(datasets_list)}")
print(f"Response body: {json.dumps(datasets_list, indent=2)}")

print("\n" + "=" * 60)
print("STEP 12: Download endpoint test")
print("=" * 60)
req = urllib.request.Request(f'http://localhost:8000/jobs/{JOB_ID}/download', headers=headers)
try:
    resp = urllib.request.urlopen(req)
    print(f"GET /jobs/{JOB_ID}/download status: {resp.status}")
    print(f"Content-Type: {resp.headers.get('Content-Type')}")
    print(f"Content-Length: {resp.headers.get('Content-Length')}")
    download_bytes = len(resp.read())
    print(f"Downloaded bytes count: {download_bytes}")
except Exception as e:
    print(f"Download endpoint error: {e}")

conn.close()
