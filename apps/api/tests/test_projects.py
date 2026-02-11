from __future__ import annotations

from fastapi.testclient import TestClient


def _signup_and_auth(client: TestClient) -> None:
    r = client.post(
        "/api/auth/signup",
        json={"username": "u1", "email": "u1@example.com", "password": "Password123!"},
    )
    assert r.status_code == 200


def test_create_and_list_projects(client: TestClient) -> None:
    _signup_and_auth(client)

    r = client.get("/api/projects")
    assert r.status_code == 200
    assert r.json() == {"projects": []}

    r = client.post("/api/projects", json={"name": "金融监管应用"})
    assert r.status_code == 201
    p = r.json()
    assert p["name"] == "金融监管应用"
    assert "id" in p
    assert "created_at" in p

    r = client.get("/api/projects")
    assert r.status_code == 200
    data = r.json()
    assert len(data["projects"]) == 1
    assert data["projects"][0]["id"] == p["id"]


def test_create_project_default_name(client: TestClient) -> None:
    _signup_and_auth(client)

    r = client.post("/api/projects", json={})
    assert r.status_code == 201
    p = r.json()
    assert p["name"].startswith("新项目 ")

