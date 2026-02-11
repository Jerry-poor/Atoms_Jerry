from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, health, projects, runs
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Atoms_Jerry API",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS: allow the local web app to call the API with cookies.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_app_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.oauth_session_secret,
        same_site="lax",
        https_only=settings.env == "prod",
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

    return app


app = create_app()
