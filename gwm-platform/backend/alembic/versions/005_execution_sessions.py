"""
005_execution_sessions

Revision ID: 005
Revises: 004
Create Date: 2026-08-08

Adds tables for Build 7 Scenario Execution Engine:
  - execution_sessions
  - execution_events
  - execution_actors
  - execution_sensors
  - execution_frames
  - execution_checkpoints
  - execution_validation

SQLite-compatible: uses batch_alter_table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, Sequence[str], None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'execution_sessions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('scenario_id', sa.String(), nullable=True),
        sa.Column('world_plan_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='CREATED'),
        sa.Column('simulator_name', sa.String(), nullable=False, default='carla'),
        sa.Column('simulator_version', sa.String(), nullable=False, default='0.9.16'),
        sa.Column('map_name', sa.String(), nullable=False, default='Town01'),
        sa.Column('map_deployment_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('fixed_delta_seconds', sa.Float(), nullable=False, default=0.05),
        sa.Column('total_simulation_seconds', sa.Float(), nullable=False, default=30.0),
        sa.Column('seeds', sa.JSON(), nullable=False),
        sa.Column('session_json', sa.JSON(), nullable=False),
        sa.Column('current_frame', sa.Integer(), nullable=False, default=0),
        sa.Column('current_simulation_time_s', sa.Float(), nullable=False, default=0.0),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('warnings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_events',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, index=True),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('trigger_type', sa.String(), nullable=False),
        sa.Column('start_time_s', sa.Float(), nullable=False),
        sa.Column('duration_s', sa.Float(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.Column('affected_actor_ids', sa.JSON(), nullable=True),
        sa.Column('action', sa.JSON(), nullable=True),
        sa.Column('seed', sa.Integer(), nullable=False),
        sa.Column('executed', sa.Boolean(), nullable=False, default=False),
        sa.Column('execution_time_s', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_actors',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, index=True),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('actor_type', sa.String(), nullable=False),
        sa.Column('semantic_class', sa.String(), nullable=False),
        sa.Column('blueprint_id', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, default='traffic'),
        sa.Column('position_x', sa.Float(), nullable=False, default=0.0),
        sa.Column('position_y', sa.Float(), nullable=False, default=0.0),
        sa.Column('position_z', sa.Float(), nullable=False, default=0.0),
        sa.Column('rotation_deg', sa.Float(), nullable=False, default=0.0),
        sa.Column('speed_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('status', sa.String(), nullable=False, default='SPAWNED'),
        sa.Column('behavior_profile', sa.JSON(), nullable=True),
        sa.Column('seed', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_sensors',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, index=True),
        sa.Column('sensor_id', sa.String(), nullable=False),
        sa.Column('sensor_type', sa.String(), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=False, default=0.0),
        sa.Column('position_y', sa.Float(), nullable=False, default=0.0),
        sa.Column('position_z', sa.Float(), nullable=False, default=0.0),
        sa.Column('rotation_pitch', sa.Float(), nullable=False, default=0.0),
        sa.Column('rotation_yaw', sa.Float(), nullable=False, default=0.0),
        sa.Column('rotation_roll', sa.Float(), nullable=False, default=0.0),
        sa.Column('resolution_w', sa.Integer(), nullable=True),
        sa.Column('resolution_h', sa.Integer(), nullable=True),
        sa.Column('fov', sa.Float(), nullable=True),
        sa.Column('frequency_hz', sa.Float(), nullable=False, default=10.0),
        sa.Column('calibration', sa.JSON(), nullable=True),
        sa.Column('healthy', sa.Boolean(), nullable=False, default=True),
        sa.Column('frame_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_frames',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, index=True),
        sa.Column('frame_id', sa.Integer(), nullable=False),
        sa.Column('simulation_time_s', sa.Float(), nullable=False),
        sa.Column('wall_time_s', sa.Float(), nullable=True),
        sa.Column('sensor_data', sa.JSON(), nullable=True),
        sa.Column('event_ids', sa.JSON(), nullable=True),
        sa.Column('actor_states', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_checkpoints',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, index=True),
        sa.Column('checkpoint_id', sa.String(), nullable=False),
        sa.Column('simulation_frame', sa.Integer(), nullable=False, default=0),
        sa.Column('simulation_time_s', sa.Float(), nullable=False, default=0.0),
        sa.Column('actor_states', sa.JSON(), nullable=True),
        sa.Column('event_state', sa.JSON(), nullable=True),
        sa.Column('random_state', sa.JSON(), nullable=True),
        sa.Column('sensor_state', sa.JSON(), nullable=True),
        sa.Column('output_state', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'execution_validation',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('session_id', sa.String(), sa.ForeignKey('execution_sessions.id'), nullable=False, unique=True),
        sa.Column('passed', sa.Boolean(), nullable=False, default=False),
        sa.Column('expected_frames', sa.Integer(), nullable=False, default=0),
        sa.Column('actual_frames', sa.Integer(), nullable=False, default=0),
        sa.Column('missing_frames', sa.JSON(), nullable=True),
        sa.Column('corrupt_files', sa.JSON(), nullable=True),
        sa.Column('sensor_sync', sa.Boolean(), nullable=False, default=False),
        sa.Column('metadata_complete', sa.Boolean(), nullable=False, default=False),
        sa.Column('provenance_complete', sa.Boolean(), nullable=False, default=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('execution_validation')
    op.drop_table('execution_checkpoints')
    op.drop_table('execution_frames')
    op.drop_table('execution_sensors')
    op.drop_table('execution_actors')
    op.drop_table('execution_events')
    op.drop_table('execution_sessions')
