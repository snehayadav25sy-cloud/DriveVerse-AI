"""spec_align_job_and_dataset

Revision ID: 133676c573e6
Revises: 392622a58f36
Create Date: 2026-07-15

SQLite-compatible migration:
- Jobs: rename/remove scenario/weather/road_type -> map/sensor; frames stays Float (SQLite)
- Datasets: add path/sensor/frame_count, remove file_path
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '133676c573e6'
down_revision: Union[str, Sequence[str], None] = '392622a58f36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    SQLite does not support ALTER COLUMN or DROP COLUMN directly.
    We use the table-copy strategy: create new table, copy data, drop old, rename.
    """
    conn = op.get_bind()

    # ── JOBS table ──────────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE jobs_new (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id),
            status TEXT DEFAULT 'queued',
            progress REAL DEFAULT 0.0,
            map TEXT DEFAULT 'Town01',
            sensor TEXT DEFAULT 'rgb',
            frames INTEGER DEFAULT 500,
            output_path TEXT,
            created_at DATETIME
        )
    """))

    # Copy existing rows; fill new columns with sensible defaults
    conn.execute(sa.text("""
        INSERT INTO jobs_new (id, project_id, status, progress, map, sensor, frames, output_path, created_at)
        SELECT
            id,
            project_id,
            LOWER(COALESCE(status, 'queued')),
            COALESCE(progress, 0.0),
            'Town01',
            'rgb',
            CAST(COALESCE(frames, 500) AS INTEGER),
            output_path,
            created_at
        FROM jobs
    """))

    op.drop_table('jobs')
    conn.execute(sa.text("ALTER TABLE jobs_new RENAME TO jobs"))

    # ── DATASETS table ───────────────────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE datasets_new (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES jobs(id),
            sensor TEXT DEFAULT 'rgb',
            path TEXT DEFAULT '',
            frame_count INTEGER DEFAULT 0,
            created_at DATETIME
        )
    """))

    # Copy existing rows — map old file_path -> path
    conn.execute(sa.text("""
        INSERT INTO datasets_new (id, job_id, sensor, path, frame_count, created_at)
        SELECT
            id,
            job_id,
            COALESCE(sensor, 'rgb'),
            COALESCE(file_path, ''),
            COALESCE(frame_count, 0),
            created_at
        FROM datasets
    """))

    op.drop_table('datasets')
    conn.execute(sa.text("ALTER TABLE datasets_new RENAME TO datasets"))


def downgrade() -> None:
    """Reverse: restore original schema (best-effort)."""
    conn = op.get_bind()

    conn.execute(sa.text("""
        CREATE TABLE jobs_old (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(id),
            status TEXT DEFAULT 'Pending',
            progress REAL DEFAULT 0.0,
            scenario TEXT,
            weather TEXT,
            road_type TEXT,
            frames REAL,
            output_path TEXT,
            created_at DATETIME
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO jobs_old (id, project_id, status, progress, scenario, weather, road_type, frames, output_path, created_at)
        SELECT id, project_id, status, progress, map, 'ClearNoon', 'City Street', frames, output_path, created_at
        FROM jobs
    """))
    op.drop_table('jobs')
    conn.execute(sa.text("ALTER TABLE jobs_old RENAME TO jobs"))

    conn.execute(sa.text("""
        CREATE TABLE datasets_old (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES jobs(id),
            sensor TEXT,
            file_path TEXT,
            frame_count INTEGER DEFAULT 0,
            created_at DATETIME
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO datasets_old (id, job_id, sensor, file_path, frame_count, created_at)
        SELECT id, job_id, sensor, path, frame_count, created_at
        FROM datasets
    """))
    op.drop_table('datasets')
    conn.execute(sa.text("ALTER TABLE datasets_old RENAME TO datasets"))
