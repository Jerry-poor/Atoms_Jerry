from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from alembic.config import Config

from alembic import command

logger = logging.getLogger(__name__)


def main() -> None:
    # Local dev convenience: load repo/root `.env` if present.
    # Keep `override=False` so explicitly exported env vars always win.
    try:
        from dotenv import find_dotenv, load_dotenv

        env_path = find_dotenv(filename=".env", raise_error_if_not_found=False)
        if env_path:
            load_dotenv(env_path, override=False)
    except Exception:
        logger.debug("Failed to load .env (dev convenience)", exc_info=True)

    # E2E convenience: Playwright starts the devserver with a SQLite DATABASE_URL.
    # If a previous run crashed mid-migration, the DB can be left half-upgraded and
    # Alembic will fail on the next boot. For test env, always start from a clean file.
    if (os.getenv("ENV") or "").strip().lower() == "test":
        db_url = (os.getenv("DATABASE_URL") or "").strip()
        if db_url.startswith("sqlite:///"):
            db_path = db_url.removeprefix("sqlite:///")
            if db_path and db_path != ":memory:":
                p = Path(db_path)
                if not p.is_absolute():
                    p = (Path.cwd() / p).resolve()
                try:
                    if p.exists():
                        p.unlink()
                    j = Path(str(p) + "-journal")
                    if j.exists():
                        j.unlink()
                except Exception:
                    logger.debug("Failed to reset SQLite test DB", exc_info=True)

    # Dev convenience: ensure migrations are applied before serving.
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

    host = os.getenv("API_HOST") or os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT") or os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
