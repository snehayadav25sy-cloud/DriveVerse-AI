"""
Diagnostic v2: launch CARLA 0.9.16, poll get_world() with retries.
"""
import subprocess, time, sys

CARLA_EXE = r"C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16\CarlaUE4.exe"

subprocess.call("taskkill /f /im CarlaUE4.exe", shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

print(f"LAUNCHING CARLA 0.9.16: {CARLA_EXE}")
proc = subprocess.Popen(
    [CARLA_EXE, "-quality-level=Low", "-RenderOffScreen"],
    creationflags=0x00000008,   # DETACHED_PROCESS
)
print(f"CARLA PID: {proc.pid}")

import carla

# Step 1: poll get_server_version until reachable
connected = False
client_ref = None
for i in range(30):
    time.sleep(3)
    try:
        c = carla.Client("localhost", 2000)
        c.set_timeout(5.0)
        ver = c.get_server_version()
        print(f"CONNECTED (get_server_version): {ver}")
        client_ref = c
        connected = True
        break
    except Exception as e:
        print(f"Attempt {i+1}/30 get_server_version: {e}")

if not connected:
    print("ERROR: CARLA never answered get_server_version.")
    sys.exit(1)

print(f"\nRAW client_version : {client_ref.get_client_version()}")
print(f"RAW server_version : {client_ref.get_server_version()}")

# Step 2: poll get_world() with retries — it takes longer than get_server_version()
print("\nPolling get_world() with 5s timeout per attempt, up to 60 attempts (5 min)...")
world = None
client_ref.set_timeout(5.0)
for i in range(60):
    try:
        world = client_ref.get_world()
        print(f"get_world() SUCCEEDED on attempt {i+1}")
        break
    except Exception as e:
        print(f"Attempt {i+1}/60 get_world: {e}")
        time.sleep(2)

if world is None:
    print("ERROR: get_world() never succeeded.")
    sys.exit(1)

# Step 3: check synchronous_mode
settings = world.get_settings()
print(f"\nRAW synchronous_mode      : {settings.synchronous_mode}")
print(f"RAW fixed_delta_seconds   : {settings.fixed_delta_seconds}")

if settings.synchronous_mode:
    print("\nWARNING: synchronous_mode is ON — resetting.")
    settings.synchronous_mode   = False
    settings.fixed_delta_seconds = 0.0
    world.apply_settings(settings)
    settings2 = world.get_settings()
    print(f"CONFIRMED synchronous_mode after reset: {settings2.synchronous_mode}")
else:
    print("\nsynchronous_mode is OFF — world is clean.")

print("\nDIAGNOSTIC COMPLETE — safe to proceed with Phase 7 test.")
