"""Pytest fixtures for backend tests.

These tests use a separate PostgreSQL test database (`blacksharkcars_test`)
so that the production / development database isn't disturbed. The fixture
creates the test DB on session start, builds the schema, and drops it on
teardown.
"""
import os
os.environ.setdefault("APP_ENV", "testing")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.core.security import hash_password
from app.models import User, Role, UserRole, Permission, RolePermission, Category, Make, Model, Location


def _build_test_database_url() -> str:
    base = os.environ.get("TEST_DATABASE_URL")
    if base:
        return base
    db_url = settings.DATABASE_URL
    head, _, tail = db_url.rpartition("/")
    if not head or not tail:
        return db_url
    if "?" in tail:
        db_name, _, qs = tail.partition("?")
        return f"{head}/{db_name}_test?{qs}"
    return f"{head}/{tail}_test"


TEST_DATABASE_URL = _build_test_database_url()
TEST_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[-1].split("?")[0]
ADMIN_DATABASE_URL = TEST_DATABASE_URL.replace(f"/{TEST_DB_NAME}", "/postgres")


def _ensure_test_database() -> None:
    """Create the test database if it doesn't exist."""
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT", future=True)
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()


def _new_test_engine():
    """Build a fresh engine. Recreating per fixture prevents pool staleness."""
    return create_engine(TEST_DATABASE_URL, pool_pre_ping=True, future=True)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    _ensure_test_database()

    # Use a dedicated admin connection to drop and recreate the schema so we
    # don't fight with SQLAlchemy's connection pool.
    admin_engine = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT", future=True)
    with admin_engine.connect() as conn:
        # Terminate any other connections to the test DB so DROP SCHEMA
        # CASCADE can succeed without blocking.
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :n AND pid <> pg_backend_pid()"
        ), {"n": TEST_DB_NAME})
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    admin_engine.dispose()

    # Build tables using a fresh engine (avoids any stale pool from module-import time).
    create_engine_ = _new_test_engine()
    Base.metadata.create_all(bind=create_engine_)
    create_engine_.dispose()
    yield

    # Tear down: drop the test database entirely.
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT", future=True)
    with admin_engine.connect() as conn:
        conn.execute(text(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = :n AND pid <> pg_backend_pid()"
        ), {"n": TEST_DB_NAME})
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))
    admin_engine.dispose()


@pytest.fixture
def db() -> Session:
    engine = _new_test_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def client(monkeypatch):
    # Stop the lifespan from running Base.metadata.create_all() against the
    # production engine, which may point to a database that doesn't exist or
    # is in a broken state.  We do all the schema setup ourselves via the
    # ``setup_database`` session fixture, so the app's startup just needs to
    # bootstrap the in-memory data (roles, permissions, super-admin).
    from app import main as app_main
    monkeypatch.setattr(app_main.Base.metadata, "create_all", lambda *a, **kw: None)

    engine = _new_test_engine()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def seeded_basics(db):
    """Create a baseline set of catalog data + permissions/roles."""
    perm = db.query(Permission).filter(Permission.code == "VIEW_LISTINGS").first()
    if not perm:
        perm = Permission(code="VIEW_LISTINGS", name="View Listings", category="listings")
        db.add(perm)
        db.flush()

    user_role = db.query(Role).filter(Role.slug == "USER").first()
    if not user_role:
        user_role = Role(name="User", slug="USER", is_system=True)
        db.add(user_role)
    admin_role = db.query(Role).filter(Role.slug == "ADMIN").first()
    if not admin_role:
        admin_role = Role(name="Admin", slug="ADMIN", is_system=True)
        db.add(admin_role)
    super_role = db.query(Role).filter(Role.slug == "SUPER_ADMIN").first()
    if not super_role:
        super_role = Role(name="Super Admin", slug="SUPER_ADMIN", is_system=True)
        db.add(super_role)
    db.flush()

    # Make sure admin role has the VIEW_LISTINGS permission.
    if not any(rp.permission_id == perm.id for rp in admin_role.permissions):
        db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        db.flush()

    cat = db.query(Category).filter(Category.slug == "sedan").first()
    if not cat:
        cat = Category(name="Sedan", slug="sedan")
        db.add(cat)
    mk = db.query(Make).filter(Make.slug == "bmw").first()
    if not mk:
        mk = Make(name="BMW", slug="bmw")
        db.add(mk)
    db.flush()
    m = db.query(Model).filter(Model.make_id == mk.id, Model.slug == "3-series").first()
    if not m:
        m = Model(make_id=mk.id, name="3 Series", slug="3-series")
        db.add(m)
    loc = db.query(Location).filter(Location.country == "USA", Location.city == "NY").first()
    if not loc:
        loc = Location(country="USA", city="NY", display_name="NY, USA")
        db.add(loc)
    db.commit()
    return {
        "permission_id": str(perm.id),
        "user_role_id": str(user_role.id),
        "admin_role_id": str(admin_role.id),
        "super_role_id": str(super_role.id),
        "category_id": str(cat.id),
        "make_id": str(mk.id),
        "model_id": str(m.id),
        "location_id": str(loc.id),
    }


@pytest.fixture
def make_user(db, seeded_basics):
    def _make(email="user@example.com", role_slug="USER", password="Test12345"):
        role = db.query(Role).filter(Role.slug == role_slug).first()
        u = User(email=email, password_hash=hash_password(password), full_name=email.split("@")[0].title())
        u.roles.append(UserRole(role=role))
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    return _make


@pytest.fixture
def auth_headers():
    def _headers(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _headers
