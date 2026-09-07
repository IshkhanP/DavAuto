"""Authentication tests."""
from app.core.security import hash_password


def test_register_login_refresh_flow(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "Sup3rPass",
        "full_name": "New User",
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["email"] == "newuser@example.com"
    assert "USER" in data["roles"]

    # login
    r = client.post("/api/v1/auth/login", json={
        "email": "newuser@example.com",
        "password": "Sup3rPass",
    })
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    # me
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "newuser@example.com"

    # refresh
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text
    new_tokens = r.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # logout
    r = client.post("/api/v1/auth/logout", json={"refresh_token": new_tokens["refresh_token"]},
                    headers={"Authorization": f"Bearer {new_tokens['access_token']}"})
    assert r.status_code == 204


def test_login_wrong_password(client, make_user):
    make_user(email="wp@example.com", role_slug="USER", password="Sup3rPass")
    r = client.post("/api/v1/auth/login", json={"email": "wp@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_weak_password_rejected(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
        "full_name": "Weak Password",
    })
    assert r.status_code == 422
