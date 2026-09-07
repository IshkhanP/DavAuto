# BlackSharkCars — Backend

FastAPI + SQLAlchemy 2 + PostgreSQL backend for the BlackSharkCars
automotive marketplace.

## Quick start

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt

# Create DB
alembic upgrade head
python -m scripts.seed

# Run
uvicorn app.main:app --reload
```

## API

* Swagger UI: `http://localhost:8000/docs`
* ReDoc:      `http://localhost:8000/redoc`
* Version:    `/api/v1`

See `app/api/v1/` for endpoint definitions.

## Development Credentials (CHANGE BEFORE PRODUCTION)

| Role        | Email                              | Password        |
|-------------|------------------------------------|-----------------|
| Super Admin | admin@blacksharkcars.local         | ChangeMe!2025   |
| User        | user@blacksharkcars.local          | Demo!2025       |
| Seller      | seller@blacksharkcars.local        | Demo!2025       |
| Dealer      | dealer@blacksharkcars.local        | Demo!2025       |

## Tests

```bash
pytest -q
```