"""
Launch CarlaUE4.exe in the background and poll until it is reachable on port 2000.
"""
import subprocess, time, sys

CARLA_EXE = r"C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16\CarlaUE4.exe"

# Kill any stale CARLA processes first
subprocess.call("taskkill /f /im CarlaUE4.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

print(f"LAUNCHING CARLA: {CARLA_EXE}")
# DETACHED_PROCESS keeps the child alive after parent exits
proc = subprocess.Popen(
    [CARLA_EXE, "-quality-level=Low", "-RenderOffScreen"],
    creationflags=0x00000008,  # DETACHED_PROCESS only
)
print(f"CARLA PID: {proc.pid}")

# Poll until server is reachable (max 90 s, 3 s between attempts)
import carla
for i in range(30):
    time.sleep(3)
    try:
        client = carla.Client("localhost", 2000)
        client.set_timeout(3.0)
        ver = client.get_server_version()
        print(f"CONNECTED TO CARLA: {ver}")
        sys.exit(0)
    except Exception as e:
        print(f"Attempt {i+1}/30: waiting... ({e})")

print("CARLA did not become reachable within 90 s")
sys.exit(1)
