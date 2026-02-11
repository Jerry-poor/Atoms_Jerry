from __future__ import annotations

import uuid


def _signup(client, suffix: str):
    username = f"u{suffix}"
    email = f"{username}@example.com"
    r = client.post("/api/auth/signup", json={"username": username, "email": email, "password": "password123"})
    assert r.status_code == 200
    return r.json()["user"]["id"]


def test_create_run_and_view_events_and_artifacts(client):
    _signup(client, uuid.uuid4().hex[:8])

    r = client.post("/api/runs", json={"input": "hello"})
    assert r.status_code == 201
    run_id = r.json()["id"]

    r = client.get(f"/api/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["status"] in {"queued", "running", "succeeded", "failed"}

    r = client.get(f"/api/runs/{run_id}/events")
    assert r.status_code == 200
    assert len(r.json()["events"]) >= 1

    r = client.get(f"/api/runs/{run_id}/artifacts")
    assert r.status_code == 200
    assert len(r.json()["artifacts"]) >= 0

    # In tests the workflow uses deterministic fallbacks; ensure it still produces at least one code artifact.
    # Background tasks run after the response; poll briefly for artifacts to appear.
    for _ in range(30):
        r = client.get(f"/api/runs/{run_id}/artifacts")
        arts = r.json()["artifacts"]
        if any(a["name"] != "final_output.json" for a in arts):
            break
    else:
        raise AssertionError("Expected generated file artifacts")


def test_create_run_team_mode(client):
    _signup(client, uuid.uuid4().hex[:8])

    r = client.post(
        "/api/runs",
        json={
            "input": "build a landing page",
            "mode": "team",
            "roles": [
                "team_lead",
                "seo_expert",
                "product_manager",
                "architect",
                "engineer",
                "data_analyst",
                "deep_researcher",
            ],
        },
    )
    assert r.status_code == 201


def test_create_run_rejects_invalid_mode(client):
    _signup(client, uuid.uuid4().hex[:8])
    r = client.post("/api/runs", json={"input": "x", "mode": "nope"})
    assert r.status_code == 400


def test_run_permissions(client):
    _signup(client, "a" + uuid.uuid4().hex[:6])
    r = client.post("/api/runs", json={"input": "private"})
    run_id = r.json()["id"]

    # new client with a new user
    client2 = client.__class__(client.app)
    _signup(client2, "b" + uuid.uuid4().hex[:6])

    r = client2.get(f"/api/runs/{run_id}")
    assert r.status_code == 403
