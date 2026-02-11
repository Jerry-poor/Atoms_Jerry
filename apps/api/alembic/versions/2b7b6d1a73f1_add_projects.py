"""add projects

Revision ID: 2b7b6d1a73f1
Revises: cc8f1a2b9b7a
Create Date: 2026-02-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2b7b6d1a73f1"
down_revision = "cc8f1a2b9b7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
