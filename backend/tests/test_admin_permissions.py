"""Authorization tests: ensure non-admin can't reach admin endpoints, admin can't reach super-admin."""
from app.models import Role


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()


def test_user_cannot_reach_admin(client, make_user):
    make_user(email="u1@example.com", role_slug="USER")
    t = _login(client, "u1@example.com", "Test12345")
    h = {"Authorization": f"Bearer {t['access_token']}"}
    r = client.get("/api/v1/admin/stats", headers=h)
    assert r.status_code == 403


def test_user_cannot_reach_super_admin(client, make_user):
    make_user(email="u2@example.com", role_slug="USER")
    t = _login(client, "u2@example.com", "Test12345")
    h = {"Authorization": f"Bearer {t['access_token']}"}
    r = client.get("/api/v1/super-admin/admins", headers=h)
    assert r.status_code == 403


def test_admin_cannot_reach_super_admin(client, make_user):
    make_user(email="admin1@example.com", role_slug="ADMIN")
    t = _login(client, "admin1@example.com", "Test12345")
    h = {"Authorization": f"Bearer {t['access_token']}"}
    r = client.get("/api/v1/super-admin/admins", headers=h)
    assert r.status_code == 403


def test_unauthenticated_blocked(client):
    r = client.get("/api/v1/admin/users")
    assert r.status_code == 401


def test_user_cannot_grant_super_admin(client, make_user, db, seeded_basics):
    # Try via admin endpoint - even ADMIN role shouldn't be able to grant SUPER_ADMIN
    target = make_user(email="admin2@example.com", role_slug="ADMIN")
    t = _login(client, "admin2@example.com", "Test12345")
    h = {"Authorization": f"Bearer {t['access_token']}"}
    super_role = db.query(Role).filter(Role.slug == "SUPER_ADMIN").first()
    r = client.patch(f"/api/v1/admin/users/{target.id}", json={"role_id": str(super_role.id)},
                     headers=h)
    # Either 403 (no permission) or 400 (admin can't assign SUPER_ADMIN per business rule)
    assert r.status_code in (400, 403)
