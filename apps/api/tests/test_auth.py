from __future__ import annotations

import uuid


def test_signup_login_logout_me(client):
    suffix = uuid.uuid4().hex[:8]
    r = client.post(
        "/api/auth/signup",
        json={"username": f"jerry{suffix}", "email": f"jerry{suffix}@example.com", "password": "password123"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == f"jerry{suffix}@example.com"

    r = client.get("/api/auth/me")
    assert r.status_code == 200

    r = client.post("/api/auth/logout")
    assert r.status_code == 200

    r = client.get("/api/auth/me")
    assert r.status_code == 401

    r = client.post(
        "/api/auth/login", json={"email": f"jerry{suffix}@example.com", "password": "password123"}
    )
    assert r.status_code == 200

    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["user"]["email"] == f"jerry{suffix}@example.com"


def test_oauth_test_mode_google_and_github(client):
    r = client.get("/api/auth/oauth/google/start", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location", "").endswith("/app")

    r = client.get("/api/auth/me")
    assert r.status_code == 200


def test_password_reset_flow(client):
    suffix = uuid.uuid4().hex[:8]
    username = f"jerry{suffix}"
    email = f"{username}@example.com"
    password = "password123"
    new_password = "newpassword123"

    r = client.post("/api/auth/signup", json={"username": username, "email": email, "password": password})
    assert r.status_code == 200

    r = client.post("/api/auth/password-reset/request", json={"email": email})
    assert r.status_code == 200
    token = r.json().get("reset_token")
    assert token

    r = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": new_password})
    assert r.status_code == 200

    # Token is single-use.
    r = client.post("/api/auth/password-reset/confirm", json={"token": token, "new_password": "anotherpass123"})
    assert r.status_code == 400

    # Old password no longer works.
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 400

    # New password works.
    r = client.post("/api/auth/login", json={"email": email, "password": new_password})
    assert r.status_code == 200


def test_password_reset_request_unknown_email_does_not_leak(client):
    r = client.post("/api/auth/password-reset/request", json={"email": f"nope-{uuid.uuid4().hex[:8]}@example.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json().get("reset_token") is None

    client.post("/api/auth/logout")

    r = client.get("/api/auth/oauth/github/start", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location", "").endswith("/app")

    r = client.get("/api/auth/me")
    assert r.status_code == 200
