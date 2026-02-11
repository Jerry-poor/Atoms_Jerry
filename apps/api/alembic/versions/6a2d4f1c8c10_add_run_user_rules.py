"""add run user_rules

Revision ID: 6a2d4f1c8c10
Revises: 4b5c1a7d7d20
Create Date: 2026-02-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "6a2d4f1c8c10"
down_revision = "4b5c1a7d7d20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("user_rules", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("runs", "user_rules")

