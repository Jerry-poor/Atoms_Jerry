from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models.oauth_account import OAuthAccount
from app.db.models.password_reset_token import PasswordResetToken
from app.db.models.session import Session as DbSession
from app.db.models.user import User
from app.services.security import hash_password, verify_password

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthResult:
    user: User
    session: DbSession


def _now() -> datetime:
    return datetime.now(tz=UTC)


class AuthService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def create_session(self, db: Session, user: User) -> DbSession:
        session = DbSession(
            id=uuid4(),
            user_id=user.id,
            expires_at=_now() + timedelta(seconds=self._settings.session_max_age_seconds),
            revoked_at=None,
        )
        db.add(session)
        db.flush()
        return session

    def revoke_session(self, db: Session, session_id: UUID) -> None:
        session = db.get(DbSession, session_id)
        if not session:
            return
        session.revoked_at = _now()
        db.add(session)

    def signup_with_password(self, db: Session, username: str, email: str, password: str) -> AuthResult:
        existing = (
            db.execute(select(User).where((User.email == email) | (User.username == username))).scalars().first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account already exists",
            )

        user = User(email=email, username=username, password_hash=hash_password(password))
        db.add(user)
        db.flush()
        session = self.create_session(db, user)
        return AuthResult(user=user, session=session)

    def login_with_password(self, db: Session, email: str, password: str) -> AuthResult:
        user = db.execute(select(User).where(User.email == email)).scalars().first()
        if not user or not user.password_hash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

        session = self.create_session(db, user)
        return AuthResult(user=user, session=session)

    def upsert_oauth_user(
        self,
        db: Session,
        provider: str,
        provider_account_id: str,
        provider_email: str | None,
        username_hint: str | None = None,
    ) -> AuthResult:
        account = (
            db.execute(
                select(OAuthAccount)
                .where(OAuthAccount.provider == provider, OAuthAccount.provider_account_id == provider_account_id)
            )
            .scalars()
            .first()
        )
        if account:
            user = db.get(User, account.user_id)
            if not user:
                # Data drift: OAuthAccount exists but User row is gone. Self-heal by recreating the user.
                logger.error(
                    "OAuthAccount missing associated User; recreating user",
                    extra={
                        "provider": provider,
                        "provider_account_id": provider_account_id,
                        "oauth_account_id": str(account.id),
                    },
                )
                db.delete(account)
                db.flush()
            else:
                # Opportunistically fill missing fields.
                if provider_email and not user.email:
                    user.email = provider_email
                db.add(user)
                session = self.create_session(db, user)
                return AuthResult(user=user, session=session)

        # Create new user
        user = User(email=provider_email, username=username_hint, password_hash=None)
        db.add(user)
        db.flush()
        account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_email=provider_email,
        )
        db.add(account)
        session = self.create_session(db, user)
        return AuthResult(user=user, session=session)

    @staticmethod
    def _hash_reset_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_password_reset_token(self, db: Session, email: str) -> str | None:
        """Create a single-use password reset token for the given email.

        Returns the raw token (caller decides whether to reveal it). If the user does not
        exist, returns None while keeping behavior safe for clients (they should still
        show a generic success message).
        """

        user = db.execute(select(User).where(User.email == email)).scalars().first()
        if not user:
            return None

        token = secrets.token_urlsafe(32)
        token_hash = self._hash_reset_token(token)
        expires_at = _now() + timedelta(hours=1)

        db.add(
            PasswordResetToken(
                id=uuid4(),
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                used_at=None,
            )
        )
        db.flush()
        return token

    def reset_password_with_token(self, db: Session, token: str, new_password: str) -> None:
        now = _now()
        token_hash = self._hash_reset_token(token)
        prt = (
            db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > now,
                )
            )
            .scalars()
            .first()
        )
        if not prt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = db.get(User, prt.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Update password + revoke existing sessions.
        user.password_hash = hash_password(new_password)
        db.add(user)

        sessions = (
            db.execute(
                select(DbSession).where(
                    DbSession.user_id == user.id,
                    DbSession.revoked_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        for s in sessions:
            s.revoked_at = now
            db.add(s)

        prt.used_at = now
        db.add(prt)
