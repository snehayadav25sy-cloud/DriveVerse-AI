# CARLA Storage Audit Report
**Generated:** 2026-08-12  
**System:** Windows 11  
**DriveVerse AI Project:** C:\Users\sneha_nqarngz\Downloads\driveverseAI  
**Working CARLA:** C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16  

---

## 1. Disk Space Summary

| Drive | Total (GB) | Used (GB) | Free (GB) |
|-------|-----------|-----------|-----------|
| C:    | 475.25    | 473.47    | **1.78**  |
| D:    | N/A       | N/A       | N/A       |

**No other drives available.**  
**Current free space: 1.78 GB**  
**CARLA size: 18.07 GB**  
**Minimum free space needed for CARLA copy + buffer: ~30 GB**

---

## 2. Largest Directories on C:

### Downloads Folder
| Directory | Size (GB) | Git Repo | Notes |
|-----------|-----------|----------|-------|
| toonengine | 76.40 | No | Data processing project, no source control |
| vector | 25.91 | No | Contains `tagged-anime-illustrations.zip` (23.37 GB) |
| SafeRoadAI | 24.59 | No | AI project with backend/frontend |
| CARLA_0.9.16 | 18.07 | No | **Working CARLA installation — DO NOT DELETE** |
| photo_checker | 10.15 | No | Unknown project |
| ai_illustrator_agent | 8.43 | No | ML/illustration project with `.venv` |
| driveverseAI | 5.70 | No | **DriveVerse AI — DO NOT DELETE** |
| ai_illustrator_agentnew | 4.08 | No | Similar to ai_illustrator_agent |
| clientService | 1.62 | No | Service project |
| new GreenIllusions | 1.61 | No | Creative project |
| RobotDataEngine | 1.49 | **Yes** | Git repository |
| moleculeDesign | 1.37 | No | Molecule/chemistry project |
| GreenIllusions02 | 1.29 | **Yes** | Git repository |
| GreenIllusions | 1.26 | No | Creative project |
| GreenIllusions03 | 1.23 | No | Creative project |
| finalnewcall | 1.05 | No | Call/voice project |
| Various small dirs | <1.0 | Mixed | Old backups, copies, tests |

### Root / Other Locations
| Location | Size (GB) | Notes |
|----------|-----------|-------|
| ProgramData\McAfee | 13.75 | Antivirus data |
| Program Files\Adobe | 9.80 | Adobe software |
| Program Files\JetBrains | 8.24 | IDE installations |
| Program Files\Microsoft Office | 4.06 | Office suite |
| Program Files\Docker | 4.05 | Docker Desktop |
| AppData\Local\Google\Chrome | 4.63 | Chrome browser data |
| AppData\Local\Programs | 7.52 | Installed programs |
| AppData\Local\Docker | 3.53 | Docker local data |
| AppData\Roaming\npm | 3.16 | npm global packages |
| AppData\Local\Microsoft | 3.14 | Microsoft app data |
| AppData\Local\ms-playwright | 1.32 | Playwright browsers |
| AppData\Roaming\Antigravity | 1.32 | Game/app data |
| AppData\Local\uv | 1.07 | uv Python package manager cache |
| AppData\Local\Mozilla | 1.74 | Firefox data |
| AppData\Local\Packages | 1.94 | Windows Store apps |
| AppData\Local\JetBrains | 0.87 | JetBrains config/cache |
| OneDrive\Desktop | 5.94 | Desktop files synced to OneDrive |
| C:\Windows\Temp | 1.89 | System temporary files |
| C:\Users\sneha_nqarngz\AppData\Local\Temp | 0.25 | User temp files |

---

## 3. Large Disposable Files in Downloads Root

| File | Size (GB) | Disposable | Reason |
|------|-----------|------------|--------|
| CARLA_0.9.16.zip | 7.28 | Yes (after verification) | Archive of working extracted installation |
| Dachcam_dataset (1).zip | 2.63 | Yes | Old dataset archive |
| archive(6).zip | 2.29 | Yes | Old archive |
| finalnewcall (3).zip | 1.38 | Yes | Old archive; extracted folder exists |
| ideaIU-2025.2.4.exe | 1.33 | Yes | IntelliJ IDEA installer; app already installed |
| archive(13).zip | 1.18 | Yes | Old archive |
| archive(14).zip | 1.18 | Yes | Old archive |
| ideaIC-2025.2.4.exe | 0.93 | Yes | IntelliJ IDEA Community installer |
| finalnewcall (4).zip | 0.76 | Yes | Old archive |
| ai_illustrator_agent (3)(1).zip | 0.61 | Yes | Old archive |
| Docker Desktop Installer.exe | 0.58 | Yes | Docker installer; Docker already installed |
| moleculeDesign.zip | 0.49 | Yes | Old archive |
| GreenIllusions03.zip | 0.42 | Yes | Old archive |
| driveverseAI.zip | 0.21 | Yes | DriveVerse archive; source code exists |
| Various PSD/video files | ~1.5 | Maybe | User content; requires manual review |

**Total disposable archives/installers: ~22 GB**

---

## 4. Cache / Regeneratable Locations

| Location | Size (GB) | Risk | Notes |
|----------|-----------|------|-------|
| pip cache (AppData\Local\pip) | 20.37 | **Very Low** | Can regenerate; 4365 HTTP cache files |
| npm cache (AppData\Local\npm-cache) | 3.22 | **Very Low** | Can regenerate |
| npm cache (AppData\Roaming\npm) | 3.16 | **Very Low** | Global package cache |
| uv cache | 1.07 | **Very Low** | Can regenerate |
| ms-playwright cache | 1.32 | **Very Low** | Can regenerate |
| Windows Temp | 1.89 | **Very Low** | System temp files |
| User Temp (AppData\Local\Temp) | 0.25 | **Very Low** | User temp files |
| conda cache | 0.16 | **Very Low** | 146 tarballs, can regenerate |
| Chrome User Data subdirs | ~1.5 | **Low** | Browser cache only (not profiles) |

**Total safely reclaimable cache: ~28 GB**

---

## 5. Conda Environments

| Environment | Path | Size (est.) | DriveVerse Required? |
|-------------|------|-------------|----------------------|
| base | C:\Users\sneha_nqarngz\miniconda3\conda2 | Large | No |
| **carla16_env** | C:\Users\sneha_nqarngz\miniconda3\conda2\envs\carla16_env | Medium | **YES — DO NOT DELETE** |
| genai | ...\envs\genai | Medium | Unknown |
| labelimg_env | ...\envs\labelimg_env | Small | Unknown |
| myenv | ...\envs\myenv | Medium | Unknown |
| mygenaivenv | ...\envs\mygenaivenv | Medium | Unknown |
| yolov8_env | ...\envs\yolov8_env | Medium | Unknown |

**Only `carla16_env` is confirmed as required by DriveVerse/CARLA.**

---

## 6. DriveVerse Repository Structure (C:\Users\sneha_nqarngz\Downloads\driveverseAI)

- **Total size:** 5.70 GB
- **Total files:** ~21,368
- **Git repository:** Yes (presence confirmed in workspace root)
- **Python API dependencies:** Uses `carla==0.9.16`
- **CARLA path references:** Found in code/config (exact paths to be identified in Phase 1)
- **Docker:** No docker-compose or Dockerfile found in root
- **Datasets:** Located within repo or referenced externally
- **No large disposable caches identified in repo root**

**DO NOT DELETE** under any circumstances:
- All `.py`, `.tsx`, `.ts`, `.json`, `.yaml`, `.yml`, `.md` source files
- `.git` directory
- `migrations/`, `schemas/`
- `datasets/` if active
- Test suites
- Generated artifacts that are inputs to tests
- CARLA Python API bindings

---

## 7. Risk Assessment for Cleanup Candidates

| Candidate | Size (GB) | Risk Level | Verdict |
|-----------|-----------|------------|---------|
| pip cache | 20.37 | **Very Low** | ✅ SAFE to purge |
| npm cache | 3.22 | **Very Low** | ✅ SAFE to purge |
| Roaming npm cache | 3.16 | **Very Low** | ✅ SAFE to purge |
| uv cache | 1.07 | **Very Low** | ✅ SAFE to purge |
| Playwright cache | 1.32 | **Very Low** | ✅ SAFE to purge |
| Windows Temp | 1.89 | **Very Low** | ✅ SAFE to clean |
| User Temp | 0.25 | **Very Low** | ✅ SAFE to clean |
| conda cache | 0.16 | **Very Low** | ✅ SAFE to clean |
| CARLA_0.9.16.zip | 7.28 | **Low** | ✅ SAFE after CARLA copy verified |
| Old installers | ~4.5 | **Low** | ✅ SAFE if corresponding apps installed |
| Old project ZIPs | ~7.5 | **Low** | ✅ SAFE if extracted folders exist |
| CARLA_0.9.16 folder | 18.07 | **Critical** | ❌ DO NOT TOUCH |
| driveverseAI folder | 5.70 | **Critical** | ❌ DO NOT TOUCH |
| carla16_env | ~2.0 | **Critical** | ❌ DO NOT TOUCH |
| toonengine | 76.40 | **High** | ⚠️ Ambiguous — not git, no clear relation to DriveVerse |
| SafeRoadAI | 24.59 | **High** | ⚠️ Ambiguous — might be related project |
| vector (anime dataset) | 25.91 | **High** | ⚠️ Ambiguous — large dataset |
| photo_checker | 10.15 | **High** | ⚠️ Ambiguous |
| ai_illustrator_agent | 8.43 | **High** | ⚠️ Ambiguous |
| OneDrive\Desktop | 5.94 | **High** | ❌ DO NOT TOUCH without user confirmation |
| Chrome profile data | ~1.4 | **Medium** | ❌ DO NOT touch profiles; cache only |

---

## 8. Estimated Recoverable Space

### Safe Cache Cleanup (Phase 2-5)
- pip cache: 20.37 GB
- npm cache: 3.22 GB
- Roaming npm: 3.16 GB
- uv cache: 1.07 GB
- Playwright cache: 1.32 GB
- Windows Temp: 1.89 GB
- User Temp: 0.25 GB
- conda cache: 0.16 GB
- **Subtotal: ~28 GB**

### Post-CARLA-Verification Archives (Phase 6+)
- CARLA_0.9.16.zip: 7.28 GB
- Old installers: ~4.5 GB
- Old project ZIPs: ~7.5 GB
- **Subtotal: ~19 GB**

### Total Potential Recovery: ~47 GB (cache + archives)

---

## 9. Recommended Cleanup Order

1. **Phase 2:** `conda clean --all` (~0.16 GB)
2. **Phase 3:** `pip cache purge` (~20.37 GB)
3. **Phase 5:** Clean Windows Temp / cleanmgr (~1.89 GB)
4. **Phase 4:** Inspect Docker (not running; minimal impact)
5. **Phase 6:** Delete old installers and archives from Downloads root (~19 GB) **only after CARLA is copied and verified**
6. **Phase 8-9:** Copy CARLA to `C:\carla` and verify
7. **Phase 10:** Update DriveVerse references
8. **Phase 11-13:** Verify CARLA + Python API + smoke test
9. **After verification:** Delete `C:\Users\sneha_nqarngz\Downloads\CARLA_0.9.16.zip` and the old `CARLA_0.9.16` folder

---

## 10. Next Steps

- Proceed to **Phase 1** (inspect DriveVerse repository structure and CARLA references)
- Proceed to **Phase 2** (conda/pip cache cleanup)
- **STOP before deleting any project source code or archives** — confirm each candidate is disposable
