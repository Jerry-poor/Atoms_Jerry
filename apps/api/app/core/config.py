from __future__ import annotations

from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    # App
    env: str = "dev"  # dev|test|prod
    test_mode: bool = False

    # URLs
    web_app_url: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/atoms_jerry"

    # Auth/session
    session_cookie_name: str = "atoms_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7  # 7 days
    oauth_session_secret: str = "dev-oauth-session-secret-change-me"

    # OAuth (prod mode)
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # LLM (optional; used by the workflow when configured)
    deepseek_api_key: str | None = None
    deepseek_api_base: str | None = None
    deepseek_model: str | None = None


@lru_cache(maxsize=1)
def _load_dotenv_once() -> None:
    """Load repo/root `.env` for local dev convenience.

    Keep `override=False` so explicitly exported env vars always win.
    Tests should set env vars explicitly (see `apps/api/tests/conftest.py`).
    """

    try:
        from dotenv import find_dotenv, load_dotenv
    except Exception:
        return

    env_path = find_dotenv(filename=".env", raise_error_if_not_found=False)
    if env_path:
        load_dotenv(env_path, override=False)


def get_settings() -> Settings:
    # Minimal explicit env loader (keeps tests deterministic and easy to override).
    # If/when settings grow, consider migrating to `pydantic-settings`.
    import os

    _load_dotenv_once()

    def b(name: str, default: bool) -> bool:
        v = os.getenv(name)
        if v is None:
            return default
        return v.lower() in {"1", "true", "yes", "on"}

    return Settings(
        env=os.getenv("ENV", "dev"),
        test_mode=b("TEST_MODE", False),
        web_app_url=os.getenv("WEB_APP_URL", "http://localhost:3000"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/atoms_jerry",
        ),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "atoms_session"),
        session_max_age_seconds=int(os.getenv("SESSION_MAX_AGE_SECONDS", str(60 * 60 * 24 * 7))),
        oauth_session_secret=os.getenv("OAUTH_SESSION_SECRET", "dev-oauth-session-secret-change-me"),
        github_client_id=os.getenv("GITHUB_CLIENT_ID"),
        github_client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID"),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_api_base=os.getenv("DEEPSEEK_API_BASE"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL"),
    )
