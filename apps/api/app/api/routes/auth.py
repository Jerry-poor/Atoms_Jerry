from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.base_client.errors import MismatchingStateError, OAuthError

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    SignupRequest,
    UserPublic,
)
from app.services.auth_service import AuthService
from app.services.oauth_clients import get_oauth

router = APIRouter()
logger = logging.getLogger(__name__)


def _user_public(u: User) -> UserPublic:
    return UserPublic(id=str(u.id), email=u.email, username=u.username)


def _set_session_cookie(response: Response, session_id: UUID) -> None:
    settings = get_settings()
    secure = settings.env == "prod"
    response.set_cookie(
        key=settings.session_cookie_name,
        value=str(session_id),
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(key=settings.session_cookie_name, path="/")


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    auth = AuthService()
    result = auth.signup_with_password(
        db,
        username=payload.username,
        email=str(payload.email),
        password=payload.password,
    )
    db.commit()
    _set_session_cookie(response, result.session.id)
    return AuthResponse(user=_user_public(result.user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    auth = AuthService()
    result = auth.login_with_password(db, email=str(payload.email), password=payload.password)
    db.commit()
    _set_session_cookie(response, result.session.id)
    return AuthResponse(user=_user_public(result.user))


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie_name)
    if raw:
        try:
            session_id = UUID(raw)
        except ValueError:
            logger.info(
                "Invalid session cookie; cannot revoke session",
                extra={"cookie_name": settings.session_cookie_name, "raw_prefix": raw[:8]},
            )
        else:
            AuthService(settings=settings).revoke_session(db, session_id)
            db.commit()
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=AuthResponse)
def me(user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=_user_public(user))


@router.get("/oauth/{provider}/start")
async def oauth_start(provider: str, request: Request, response: Response, db: Session = Depends(get_db)):
    settings = get_settings()
    if provider not in {"google", "github"}:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider '{provider}'. Valid providers: google, github",
        )

    if settings.test_mode:
        # Deterministic fake OAuth for E2E tests.
        auth = AuthService(settings=settings)
        email = f"test-{provider}@example.com"
        result = auth.upsert_oauth_user(
            db,
            provider=provider,
            provider_account_id=f"{provider}-test-user",
            provider_email=email,
            username_hint=f"{provider}_test",
        )
        db.commit()
        redirect = RedirectResponse(url=f"{settings.web_app_url}/app", status_code=302)
        _set_session_cookie(redirect, result.session.id)
        return redirect

    # Prod/dev OAuth: ensure credentials exist.
    if provider == "google" and (not settings.google_client_id or not settings.google_client_secret):
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    if provider == "github" and (not settings.github_client_id or not settings.github_client_secret):
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

    oauth = get_oauth()
    client = oauth.create_client(provider)
    # Build callback from public web origin to avoid proxy/internal host mismatches.
    redirect_uri = f"{settings.web_app_url}/api/auth/oauth/{provider}/callback"
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if provider not in {"google", "github"}:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown provider '{provider}'. Valid providers: google, github",
        )

    if settings.test_mode:
        raise HTTPException(
            status_code=400,
            detail="OAuth callback is disabled in TEST_MODE; use /api/auth/oauth/{provider}/start instead.",
        )

    oauth = get_oauth()
    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
    except MismatchingStateError as e:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth state mismatch for {provider}; please retry from /login and avoid reusing callback URLs.",
        ) from e
    except OAuthError as e:
        msg = (str(e) or "").lower()
        if "invalid_grant" in msg:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth token exchange failed for {provider}: invalid_grant (authorization code expired/used, or callback URL mismatch).",
            ) from e
        raise HTTPException(status_code=400, detail=f"OAuth token exchange failed for {provider}: {e}") from e
    except Exception as e:
        logger.exception("OAuth authorize_access_token failed", extra={"provider": provider})
        raise HTTPException(status_code=400, detail=f"OAuth token exchange failed for {provider}") from e

    provider_account_id: str | None = None
    provider_email: str | None = None
    username_hint: str | None = None

    if provider == "google":
        userinfo = token.get("userinfo")
        if token.get("id_token"):
            try:
                # Authlib versions differ on parse_id_token signature.
                userinfo = await client.parse_id_token(request, token)
            except TypeError:
                userinfo = await client.parse_id_token(token)
            except Exception:
                logger.exception("Google parse_id_token failed; fallback to userinfo endpoint")

        if userinfo is None:
            resp = await client.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)
            if resp.status_code >= 400:
                raise HTTPException(status_code=400, detail="Google userinfo fetch failed")
            userinfo = resp.json()

        provider_account_id = str(userinfo.get("sub"))
        provider_email = userinfo.get("email")
        username_hint = userinfo.get("name") or (provider_email.split("@")[0] if provider_email else None)
    else:
        # github
        resp = await client.get("user", token=token)
        profile = resp.json()
        provider_account_id = str(profile.get("id"))
        username_hint = profile.get("login")
        provider_email = profile.get("email")
        if not provider_email:
            emails_resp = await client.get("user/emails", token=token)
            emails = emails_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            provider_email = primary.get("email") if primary else None

    if not provider_account_id:
        raise HTTPException(status_code=400, detail="OAuth profile missing id")

    auth = AuthService(settings=settings)
    result = auth.upsert_oauth_user(
        db,
        provider=provider,
        provider_account_id=provider_account_id,
        provider_email=provider_email,
        username_hint=username_hint,
    )
    db.commit()

    redirect = RedirectResponse(url=f"{settings.web_app_url}/app", status_code=302)
    _set_session_cookie(redirect, result.session.id)
    return redirect


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def password_reset_request(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> PasswordResetRequestResponse:
    """Request a password reset.

    Always returns ok=true to avoid leaking whether an email exists. In non-prod or TEST_MODE,
    the raw token is returned for local development convenience (no email delivery in this MVP).
    """

    settings = get_settings()
    auth = AuthService(settings=settings)
    token = auth.create_password_reset_token(db, email=str(payload.email))
    db.commit()
    reveal_token = settings.env != "prod" or settings.test_mode
    return PasswordResetRequestResponse(ok=True, reset_token=token if reveal_token else None)


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResponse)
def password_reset_confirm(
    payload: PasswordResetConfirmRequest,
    db: Session = Depends(get_db),
) -> PasswordResetConfirmResponse:
    settings = get_settings()
    auth = AuthService(settings=settings)
    auth.reset_password_with_token(db, token=payload.token, new_password=payload.new_password)
    db.commit()
    return PasswordResetConfirmResponse(ok=True)
