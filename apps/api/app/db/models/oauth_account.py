from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models._mixins import TimestampMixin


class OAuthAccount(Base, TimestampMixin):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_account_id", name="uq_oauth_account"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)

    provider: Mapped[str] = mapped_column(String, nullable=False)  # google|github
    provider_account_id: Mapped[str] = mapped_column(String, nullable=False)
    provider_email: Mapped[str | None] = mapped_column(String, nullable=True)

    user = relationship("User", back_populates="oauth_accounts")
