from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure `import app` works even when pytest sets CWD to `tests/`.
sys.path.append(str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="session", autouse=True)
def _test_env(tmp_path_factory: pytest.TempPathFactory) -> None:
    tmp = tmp_path_factory.mktemp("db")
    db_path = Path(tmp) / "test.db"

    # Tests must be deterministic and must not be affected by developer `.env` files.
    os.environ["ENV"] = "test"
    os.environ["TEST_MODE"] = "true"
    os.environ["WEB_APP_URL"] = "http://localhost:3000"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    # Ensure unit tests never call external LLM providers even if a developer `.env` exists.
    os.environ["DEEPSEEK_API_KEY"] = ""
    os.environ["DEEPSEEK_API_BASE"] = ""
    os.environ["DEEPSEEK_MODEL"] = ""


@pytest.fixture()
def client() -> TestClient:
    # Import after env vars are set (engine is initialized at import time).
    from app.db.base import Base
    from app.db.session import engine
    from app.main import create_app

    # Keep tests isolated: rebuild schema for each test.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app = create_app()
    return TestClient(app)
