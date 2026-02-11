from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._mixins import TimestampMixin


class Run(Base, TimestampMixin):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )

    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    mode: Mapped[str] = mapped_column(String, nullable=False, default="engineer")  # engineer|team
    roles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # Optional per-run user rule strings (parsed by Rule Node into structured rules).
    user_rules: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    # Optional: seed state + target node to re-run from a checkpoint.
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    seed_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    seed_goto: Mapped[str | None] = mapped_column(String, nullable=True)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="runs")
    events = relationship("RunEvent", back_populates="run")
    checkpoints = relationship("RunCheckpoint", back_populates="run")
    artifacts = relationship("RunArtifact", back_populates="run")
