from __future__ import annotations

import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)

    oauth_accounts = relationship("OAuthAccount", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    password_reset_tokens = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    projects = relationship("Project", back_populates="user")
    runs = relationship("Run", back_populates="user")
