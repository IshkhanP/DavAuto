"""BlackSharkCars FastAPI application entrypoint."""
from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.models import (  # noqa: F401  ensures all models are registered
    User, Role, Permission, UserRole, RolePermission, RefreshToken,
    Category, Make, Model, Location,
    Car, CarImage, CarVideo, CarFeature, Favorite,
    Conversation, ConversationParticipant, Message, Notification,
    Dealer, DealerEmployee, Report, PromotionPackage, UserPromotion,
    Payment, Review, AuditLog, SiteSetting,
)
from app.permissions.definitions import ROLE_PERMISSION_MATRIX, PERMISSION_METADATA
from app.middleware import SecurityHeadersMiddleware
from app.api import api_router

# ---- Logging configuration ----
# Logs go to BOTH stdout (for `python run.py`) and a rotating file under
# `backend/logs/blacksharkcars.log` (max 5 MB, 5 backups). The file location
# is fixed so log analysis tools can find it.
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "blacksharkcars.log")

logger = logging.getLogger("blacksharkcars")
logger.setLevel(logging.INFO)
logger.propagate = False  # avoid double-logging via uvicorn's default logger

# Reset handlers so re-imports (uvicorn reload) don't add duplicates
for _h in list(logger.handlers):
    logger.removeHandler(_h)

_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)

_file_handler = RotatingFileHandler(
    _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)

_stream_handler = logging.StreamHandler()
_stream_handler.setLevel(logging.INFO)
_stream_handler.setFormatter(_formatter)
logger.addHandler(_stream_handler)

# Also log uncaught exceptions to the file
def _log_uncaught(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

import sys as _sys
_sys.excepthook = _log_uncaught

logger.info("Logging initialized; log file: %s", _LOG_FILE)


def _ensure_storage_dir() -> None:
    if settings.STORAGE_TYPE == "local":
        os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_storage_dir()
    # Create tables on startup if they don't exist (useful for first run).
    # In production, prefer alembic upgrade head.
    if os.environ.get("AUTO_CREATE_TABLES", "true").lower() == "true":
        Base.metadata.create_all(bind=engine)
    bootstrap_roles_and_permissions()
    yield


def bootstrap_roles_and_permissions() -> None:
    """Idempotently seed permission codes, default roles, and a super admin."""
    from app.core.security import hash_password

    with SessionLocal() as db:
        # 1) Permissions
        for code, meta in PERMISSION_METADATA.items():
            existing = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
            if not existing:
                db.add(Permission(code=code, name=meta["name"], description=meta.get("description"), category=meta["category"]))
        db.flush()

        all_perms = {p.code: p for p in db.execute(select(Permission)).scalars().all()}

        # 2) Roles
        for slug, perm_codes in ROLE_PERMISSION_MATRIX.items():
            role = db.execute(select(Role).where(Role.slug == slug)).scalar_one_or_none()
            if not role:
                role = Role(name=slug.replace("_", " ").title(), slug=slug, is_system=slug in ("SUPER_ADMIN", "ADMIN", "USER", "GUEST"), is_default=slug in ("USER", "GUEST"), description=f"{slug} role")
                db.add(role)
                db.flush()
            # Sync permissions
            existing_perms = {rp.permission.code for rp in role.permissions}
            for code in perm_codes:
                if code in all_perms and code not in existing_perms:
                    db.add(RolePermission(role_id=role.id, permission_id=all_perms[code].id))
        db.flush()

        # 3) Super admin user (only on dev / when env configured)
        sa_email = settings.SUPER_ADMIN_EMAIL
        sa_password = settings.SUPER_ADMIN_PASSWORD
        sa_user = db.execute(select(User).where(User.email == sa_email.lower())).scalar_one_or_none()
        super_admin_role = db.execute(select(Role).where(Role.slug == "SUPER_ADMIN")).scalar_one_or_none()
        if sa_user and super_admin_role and not any(r.role.slug == "SUPER_ADMIN" for r in sa_user.roles):
            sa_user.roles.append(UserRole(role=super_admin_role))
        elif not sa_user and super_admin_role:
            sa_user = User(
                email=sa_email.lower(),
                password_hash=hash_password(sa_password),
                full_name="Super Admin",
                status="ACTIVE",
                is_email_verified=True,
            )
            sa_user.roles.append(UserRole(role=super_admin_role))
            db.add(sa_user)

        db.commit()


app = FastAPI(
    title="BlackSharkCars API",
    version=settings.APP_VERSION,
    description="BlackSharkCars marketplace REST API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.add_middleware(SecurityHeadersMiddleware)

# Serve uploaded files (local storage backend)
if settings.STORAGE_TYPE == "local":
    os.makedirs(settings.STORAGE_LOCAL_PATH, exist_ok=True)
    app.mount("/static", StaticFiles(directory=settings.STORAGE_LOCAL_PATH), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log validation errors so we can diagnose malformed frontend payloads.
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "validation_error", "message": "Invalid request payload", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log with full traceback to the rotating log file.
    logger.exception(
        "Unhandled exception on %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_error", "message": "An unexpected error occurred. Please try again later."},
    )


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)