from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RunCheckpoint(Base):
    __tablename__ = "run_checkpoints"
    __table_args__ = (UniqueConstraint("run_id", "seq", name="uq_run_checkpoint_seq"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("runs.id"), nullable=False)

    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    node: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=UTC), nullable=False
    )

    run = relationship("Run", back_populates="checkpoints")
