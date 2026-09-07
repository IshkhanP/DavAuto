"""Security primitives: password hashing and JWT helpers."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import secrets

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def _create_token(
    subject: str,
    secret: str,
    expires_delta: timedelta,
    token_type: str,
    extra_claims: Optional[dict] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, settings.JWT_SECRET_KEY, delta, "access", extra_claims)


def create_refresh_token(
    subject: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    delta = expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, settings.JWT_REFRESH_SECRET_KEY, delta, "refresh", extra_claims)


def decode_token(token: str, secret: str) -> Optional[dict]:
    try:
        return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    return decode_token(token, settings.JWT_SECRET_KEY)


def decode_refresh_token(token: str) -> Optional[dict]:
    return decode_token(token, settings.JWT_REFRESH_SECRET_KEY)


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)