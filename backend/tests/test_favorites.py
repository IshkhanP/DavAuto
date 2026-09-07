"""Favorites tests."""
def _login(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()


def test_favorite_toggle_and_unique(client, make_user, seeded_basics):
    u = make_user(email="fav@example.com", role_slug="USER")
    t = _login(client, "fav@example.com", "Test12345")
    headers = {"Authorization": f"Bearer {t['access_token']}"}

    r = client.post("/api/v1/cars", json={
        "make_id": seeded_basics["make_id"], "model_id": seeded_basics["model_id"],
        "year": 2020, "price": 12000, "mileage": 30000,
    }, headers=headers)
    car_id = r.json()["id"]

    # first add
    r = client.post(f"/api/v1/favorites/{car_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["favorited"] is True

    # adding again is a no-op
    r = client.post(f"/api/v1/favorites/{car_id}", headers=headers)
    assert r.status_code == 200

    r = client.get("/api/v1/favorites", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1

    # remove
    r = client.delete(f"/api/v1/favorites/{car_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["favorited"] is False
