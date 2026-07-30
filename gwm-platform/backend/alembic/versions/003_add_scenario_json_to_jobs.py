"""add_scenario_json_to_jobs

Revision ID: 003
Revises: 133676c573e6
Create Date: 2026-07-26

Adds a nullable JSON column `scenario_json` to the jobs table to store
the full ScenarioConfig produced by the Prompt Engine pipeline.
SQLite-compatible: uses batch_alter_table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, Sequence[str], None] = '133676c573e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on:    Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(sa.Column('scenario_json', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_column('scenario_json')
