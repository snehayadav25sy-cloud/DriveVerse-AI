# Contributing to DriveVerse AI

Thank you for contributing to DriveVerse AI! Please adhere to the following rules, coding style, and workflows to ensure zero functional regressions.

---

## 1. Setup Your Development Environment

Ensure your system aligns with our exact version pins:

* **OS:** Windows
* **Conda environment:** `carla16_env` on **Python 3.10.11**
* **CARLA Simulator Server:** Version **0.9.16** located at `C:\carla\WindowsNoEditor\CarlaUE4.exe`

Install requirements:
```bash
conda activate carla16_env
pip install -r requirements-carla.txt
```

---

## 2. Hard Constraints & Coding Rules

### A. Architectural Isolation (CARLA Imports)
* **Never** write `import carla` inside general backend routes or geography files.
* Keep simulator-specific imports inside `simulators/carla/` or `worker/simulator/carla/`.

### B. Version Pinning Discipline
* Do not upgrade the `carla` package version or any other pinned packages in `requirements-carla.txt` without checking compatibility with CARLA 0.9.16.

### C. Local VRAM Constraints
* Local GPUs (specifically 4GB VRAM mobile/laptop chips like the RTX 3050 Laptop) cannot handle custom OpenDRIVE maps. Do not change default maps in the local test suite. Any test running Ebene or Pont-Fer Roundabout maps must be flagged as `BLOCKED` unless executed on a cloud GPU instance with >=12GB VRAM.

---

## 3. Pull Request & Verification Checklist

Before proposing a merge, you must run and pass all verifications:

1. **Backend Tests:** Run the full pytest suite:
   ```bash
   conda activate carla16_env
   pytest tests/full_system/
   ```
2. **Frontend Build:** Confirm the production build of Vite builds with zero errors:
   ```bash
   cd gwm-platform/frontend
   npm run build
   ```
3. **No Dead Mock Code:** Check that `mock_capture()` or fallback logging has not sneaked back in.
4. **openapi.json Route Consistency:** Verify backend routes match the baseline specification.
