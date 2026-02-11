"""add run mode/roles/project

Revision ID: 4b5c1a7d7d20
Revises: 2b7b6d1a73f1
Create Date: 2026-02-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "4b5c1a7d7d20"
down_revision = "2b7b6d1a73f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("project_id", sa.Uuid(), nullable=True))
    op.add_column("runs", sa.Column("mode", sa.String(), nullable=False, server_default="engineer"))
    op.add_column("runs", sa.Column("roles", sa.JSON(), nullable=True))

    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        # SQLite doesn't support ALTER TABLE ADD CONSTRAINT; use batch mode copy strategy.
        with op.batch_alter_table("runs") as batch:
            batch.create_foreign_key(
                "fk_runs_project_id_projects",
                "projects",
                ["project_id"],
                ["id"],
            )
            batch.create_index(op.f("ix_runs_project_id"), ["project_id"], unique=False)
            # Remove server default after backfill.
            batch.alter_column("mode", server_default=None)
    else:
        op.create_foreign_key("fk_runs_project_id_projects", "runs", "projects", ["project_id"], ["id"])
        op.create_index(op.f("ix_runs_project_id"), "runs", ["project_id"], unique=False)

        # Remove server default after backfill.
        op.alter_column("runs", "mode", server_default=None)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        with op.batch_alter_table("runs") as batch:
            batch.drop_index(op.f("ix_runs_project_id"))
            batch.drop_constraint("fk_runs_project_id_projects", type_="foreignkey")
    else:
        op.drop_index(op.f("ix_runs_project_id"), table_name="runs")
        op.drop_constraint("fk_runs_project_id_projects", "runs", type_="foreignkey")

    op.drop_column("runs", "roles")
    op.drop_column("runs", "mode")
    op.drop_column("runs", "project_id")
