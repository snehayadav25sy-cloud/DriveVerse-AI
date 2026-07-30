# Environment — DO NOT DEVIATE

CARLA server: EXACTLY version 0.9.16, installed ONLY at C:\carla\WindowsNoEditor\CarlaUE4.exe
Do not download, reference, or launch any other CARLA installation or version.

Python client: EXACTLY carla==0.9.16, in conda env `carla16_env`.
Pinned in requirements-carla.txt.

Launch CARLA ONLY via C:\carla\start_carla.bat — never invoke CarlaUE4.exe directly from another path.

worker/simulator/carla/client.py enforces this at runtime — any version mismatch raises RuntimeError immediately rather than hanging.

If you find any other CarlaUE4.exe path or a `carla` pip version other than 0.9.16 anywhere on this system, STOP and flag it to the user — do not attempt to silently resolve it by picking either version.
