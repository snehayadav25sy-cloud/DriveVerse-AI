# Repository Cleanup Audit Report

| Path | Category | Used? | Referenced By | Safe to Move? | Safe to Delete? | Reason |
|---|---|---|---|---|---|---|
| `comprehensive_sensor_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `diag_carla.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `fix_db_schema.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `launch_carla.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `minimal_stability_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `multisensor_1frame_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `multisensor_2frame_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `multisensor_6frame_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `multisensor_frames_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `rgb_slow_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_opendrive_diagnostic.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase1_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase2_test_a.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase2_test_b.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase3_test_a.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase4_test_a.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase5_test_a.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase6_test_a.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase7_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_phase8_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_remaining_verifications.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_single_worker_job.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `run_stageA_disambiguation.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `sensors_no_listener_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `sensors_queues_test.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `submit_and_run_worker.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `validate_pipeline.py` | Diagnostic/Test Script | NO | None | YES | YES | One-off debug/validation script (referenced 0 times). |
| `gwm-platform/database` | Configuration/Directory | YES | fix_db_schema.py, run_phase1_test.py, run_phase2_test_a.py, run_phase2_test_b.py, run_phase3_test_a.py, run_phase4_test_a.py, run_phase5_test_a.py, run_phase6_test_a.py, run_phase7_test.py, run_remaining_verifications.py, run_single_worker_job.py, submit_and_run_worker.py, validate_pipeline.py, gwm-platform\backend\alembic.ini, gwm-platform\backend\main.py, gwm-platform\backend\test_e2e_country.py, gwm-platform\backend\alembic\env.py, gwm-platform\backend\alembic\README, gwm-platform\backend\app\api\analytics.py, gwm-platform\backend\app\api\auth.py, gwm-platform\backend\app\api\datasets.py, gwm-platform\backend\app\api\jobs.py, gwm-platform\backend\app\api\projects.py, gwm-platform\backend\app\api\prompt.py, gwm-platform\backend\app\database\database.py, gwm-platform\backend\app\database\__init__.py, gwm-platform\backend\app\models\dataset.py, gwm-platform\backend\app\models\job.py, gwm-platform\backend\app\models\project.py, gwm-platform\backend\app\models\prompt.py, gwm-platform\backend\app\models\prompt_history.py, gwm-platform\backend\app\models\user.py, gwm-platform\backend\app\models\world.py, gwm-platform\worker\main.py | YES | NO | Empty duplicate database dir. Safe to delete or keep as placeholder. |
| `docker-compose.yml` | Configuration/Directory | NO | None | YES | NO | Authoritative root compose config for MinIO + Postgres |