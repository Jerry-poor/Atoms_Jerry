from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.session import Session as DbSession
from app.db.models.user import User
from app.db.session import get_db

settings = get_settings()


def get_current_user(
    db: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=settings.session_cookie_name),
) -> User:
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    try:
        sid = UUID(session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized") from e

    now = datetime.now(tz=UTC)
    stmt = (
        select(User)
        .join(DbSession, DbSession.user_id == User.id)
        .where(
            DbSession.id == sid,
            DbSession.revoked_at.is_(None),
            DbSession.expires_at > now,
        )
    )
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return user
