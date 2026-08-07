"""
004_add_world_generation_tables

Revision ID: 004
Revises: 003
Create Date: 2026-08-07

Adds tables for Build 6 Procedural World Generation:
  - world_plans
  - world_provenance
  - world_artifacts

SQLite-compatible: uses batch_alter_table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, Sequence[str], None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'world_plans',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('job_id', sa.String(), sa.ForeignKey('jobs.id'), nullable=False, unique=True),
        sa.Column('world_id', sa.String(), nullable=False, index=True),
        sa.Column('world_seed', sa.Integer(), nullable=False),
        sa.Column('location_query', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('map_name', sa.String(), nullable=False),
        sa.Column('plan_json', sa.JSON(), nullable=False),
        sa.Column('plan_hash', sa.String(), nullable=False),
        sa.Column('asset_resolution_stats', sa.JSON(), nullable=True),
        sa.Column('fallbacks', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'world_provenance',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('world_plan_id', sa.String(), sa.ForeignKey('world_plans.id'), nullable=False, unique=True),
        sa.Column('build_version', sa.String(), nullable=False),
        sa.Column('country_profile_hash', sa.String(), nullable=False),
        sa.Column('geography_hash', sa.String(), nullable=False),
        sa.Column('world_plan_hash', sa.String(), nullable=False),
        sa.Column('asset_registry_hash', sa.String(), nullable=False),
        sa.Column('world_seed', sa.Integer(), nullable=False),
        sa.Column('traffic_seed', sa.Integer(), nullable=False),
        sa.Column('pedestrian_seed', sa.Integer(), nullable=False),
        sa.Column('weather_seed', sa.Integer(), nullable=False),
        sa.Column('asset_seed', sa.Integer(), nullable=False),
        sa.Column('scenario_seed', sa.Integer(), nullable=False),
        sa.Column('carla_version', sa.String(), nullable=False),
        sa.Column('git_commit', sa.String(), nullable=True),
        sa.Column('provenance_hash', sa.String(), nullable=False),
        sa.Column('fallbacks', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'world_artifacts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('world_plan_id', sa.String(), sa.ForeignKey('world_plans.id'), nullable=False),
        sa.Column('artifact_type', sa.String(), nullable=False),
        sa.Column('artifact_path', sa.String(), nullable=True),
        sa.Column('artifact_size_bytes', sa.Integer(), nullable=True),
        sa.Column('artifact_hash', sa.String(), nullable=True),
        sa.Column('artifact_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('world_artifacts')
    op.drop_table('world_provenance')
    op.drop_table('world_plans')
