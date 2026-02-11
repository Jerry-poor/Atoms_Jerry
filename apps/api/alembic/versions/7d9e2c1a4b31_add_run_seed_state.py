"""add run seed state

Revision ID: 7d9e2c1a4b31
Revises: 6a2d4f1c8c10
Create Date: 2026-02-11 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "7d9e2c1a4b31"
down_revision = "6a2d4f1c8c10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("parent_run_id", sa.Uuid(), nullable=True))
    op.add_column("runs", sa.Column("seed_state", sa.JSON(), nullable=True))
    op.add_column("runs", sa.Column("seed_goto", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "seed_goto")
    op.drop_column("runs", "seed_state")
    op.drop_column("runs", "parent_run_id")

