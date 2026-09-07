"""Car / listing tests."""
from app.models.car import Car
from app.models.enums import CarStatus


def _create_car(client, headers, make_id, model_id, category_id=None, location_id=None, price=15000, year=2020, mileage=30000):
    body = {
        "make_id": make_id,
        "model_id": model_id,
        "year": year,
        "price": price,
        "currency": "USD",
        "mileage": mileage,
        "condition": "USED",
    }
    if category_id:
        body["category_id"] = category_id
    if location_id:
        body["location_id"] = location_id
    return client.post("/api/v1/cars", json=body, headers=headers)


def test_create_car_requires_auth(client, seeded_basics):
    r = client.post("/api/v1/cars", json={
        "make_id": seeded_basics["make_id"],
        "model_id": seeded_basics["model_id"],
        "year": 2020, "price": 15000, "mileage": 30000,
    })
    assert r.status_code == 401


def test_create_and_list_car(client, make_user, seeded_basics):
    u = make_user(email="seller1@example.com", role_slug="USER")
    r = client.post("/api/v1/auth/login", json={"email": "seller1@example.com", "password": "Test12345"})
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = _create_car(client, headers, seeded_basics["make_id"], seeded_basics["model_id"], price=20000, year=2021)
    assert r.status_code == 201, r.text
    car_id = r.json()["id"]

    r = client.get("/api/v1/cars")
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(c["id"] == car_id for c in items)

    r = client.get(f"/api/v1/cars/{car_id}")
    assert r.status_code == 200
    assert r.json()["make_name"] == "BMW"


def test_filter_by_price(client, make_user, seeded_basics):
    u = make_user(email="seller2@example.com", role_slug="USER")
    r = client.post("/api/v1/auth/login", json={"email": "seller2@example.com", "password": "Test12345"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    for price in (10000, 25000, 40000):
        _create_car(client, headers, seeded_basics["make_id"], seeded_basics["model_id"], price=price, year=2021)

    r = client.get("/api/v1/cars?min_price=20000&max_price=30000")
    data = r.json()
    assert all(20000 <= c["price"] <= 30000 for c in data["items"])


def test_other_user_cannot_edit_my_car(client, make_user, seeded_basics):
    owner = make_user(email="owner@example.com", role_slug="USER")
    other = make_user(email="other@example.com", role_slug="USER")

    o = client.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": "Test12345"}).json()
    r = _create_car(client, {"Authorization": f"Bearer {o['access_token']}"}, seeded_basics["make_id"], seeded_basics["model_id"])
    car_id = r.json()["id"]

    # Try to edit as "other"
    n = client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "Test12345"}).json()
    r = client.patch(f"/api/v1/cars/{car_id}", json={"price": 1}, headers={"Authorization": f"Bearer {n['access_token']}"})
    assert r.status_code == 403
