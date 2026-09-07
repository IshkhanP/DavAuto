"""Authentication API: register, login, refresh, logout, forgot/reset password."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_refresh_token, generate_token,
)
from app.core.config import settings
from app.models.user import (
    User, UserRole, Role, RefreshToken, PasswordResetToken, EmailVerificationToken,
)
from app.models.enums import UserStatus, NotificationType
from app.permissions.rbac import get_current_user
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenPair, RefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    VerifyEmailRequest, UserPrivate, UserPublic, UpdateProfileRequest,
)
from app.services.email import email_service
from app.services.notifications import create_notification
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def _build_user_private(user: User) -> UserPrivate:
    role_slugs = [ur.role.slug for ur in user.roles]
    permissions: list[str] = []
    seen = set()
    for ur in user.roles:
        for rp in ur.role.permissions:
            if rp.permission.code not in seen:
                permissions.append(rp.permission.code)
                seen.add(rp.permission.code)
    return UserPrivate(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        city=user.city,
        country=user.country,
        status=user.status,
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
        roles=role_slugs,
        permissions=permissions,
    )


async def _issue_tokens(db: Session, user: User, request: Optional[Request] = None) -> TokenPair:
    access = create_access_token(str(user.id), extra_claims={"email": user.email})
    refresh = create_refresh_token(str(user.id))

    # Decode refresh to grab its jti so we can persist / revoke later.
    payload = decode_refresh_token(refresh)
    if not payload or "jti" not in payload:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to issue refresh token",
        )
    jti = payload["jti"]

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    ip = request.client.host if request and request.client else None
    ua = request.headers.get("user-agent") if request else None

    db.add(RefreshToken(
        user_id=user.id,
        jti=jti,
        token_hash=hash_password(refresh),
        user_agent=(ua or "")[:255],
        ip_address=ip,
        expires_at=expires_at,
    ))

    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def _get_default_role(db: Session, slug: str) -> Optional[Role]:
    return db.execute(select(Role).where(Role.slug == slug)).scalar_one_or_none()


@router.post("/register", response_model=UserPrivate, status_code=201)
async def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> UserPrivate:
    existing = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        city=payload.city,
        country=payload.country,
        status=UserStatus.ACTIVE.value,
    )

    role = await _get_default_role(db, "USER")
    if role:
        user.roles.append(UserRole(role=role))

    db.add(user)
    db.flush()

    # generate email verification token
    token = generate_token()
    db.add(EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_password(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=2),
    ))

    log_action(db, action="USER_REGISTERED", user_id=user.id, request=request)
    db.commit()
    db.refresh(user)

    await email_service.send(
        user.email,
        "Verify your BlackSharkCars email",
        f"<p>Welcome to BlackSharkCars! Verify your email with this token: <b>{token}</b></p>",
        f"Verify your email with token: {token}",
    )

    return _build_user_private(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 10:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked")

    if user.status in ("SUSPENDED", "BANNED"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account {user.status.lower()}")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None

    log_action(db, action="USER_LOGIN", user_id=user.id, request=request)
    db.commit()

    tokens = await _issue_tokens(db, user, request)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    data = decode_refresh_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    jti = data.get("jti")
    sub = data.get("sub")

    stmt = select(RefreshToken).where(RefreshToken.jti == jti)
    stored = db.execute(stmt).scalar_one_or_none()
    if not stored or stored.revoked or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or expired")

    if not verify_password(payload.refresh_token, stored.token_hash):
        stored.revoked = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.execute(select(User).where(User.id == uuid_module.UUID(sub))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # rotate: revoke old refresh
    stored.revoked = True
    tokens = await _issue_tokens(db, user, request)
    db.commit()
    return tokens


@router.post("/logout", status_code=204)
async def logout(payload: RefreshRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = decode_refresh_token(payload.refresh_token)
    if data and data.get("jti"):
        stored = db.execute(select(RefreshToken).where(RefreshToken.jti == data["jti"])).scalar_one_or_none()
        if stored:
            stored.revoked = True
            db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=204)
async def logout_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        RefreshToken.__table__.update().where(RefreshToken.user_id == user.id).values(revoked=True)
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=202)
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none()
    if user:
        token = generate_token()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hash_password(token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
        ))
        db.commit()
        await email_service.send(
            user.email,
            "Reset your BlackSharkCars password",
            f"<p>Use this token to reset your password: <b>{token}</b></p>",
            f"Reset token: {token}",
        )
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=204)
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    candidates = db.execute(select(PasswordResetToken).where(PasswordResetToken.used == False)).scalars().all()  # noqa: E712
    matched = None
    for c in candidates:
        if verify_password(payload.token, c.token_hash):
            matched = c
            break
    if not matched or matched.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.execute(select(User).where(User.id == matched.user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    matched.used = True
    db.execute(RefreshToken.__table__.update().where(RefreshToken.user_id == user.id).values(revoked=True))
    db.commit()
    return Response(status_code=204)


@router.post("/verify-email", status_code=204)
async def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    candidates = db.execute(select(EmailVerificationToken).where(EmailVerificationToken.used == False)).scalars().all()  # noqa: E712
    matched = None
    for c in candidates:
        if verify_password(payload.token, c.token_hash):
            matched = c
            break
    if not matched or matched.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.execute(select(User).where(User.id == matched.user_id)).scalar_one_or_none()
    user.is_email_verified = True
    matched.used = True
    db.commit()
    return Response(status_code=204)


@router.get("/me", response_model=UserPrivate)
async def get_me(user: User = Depends(get_current_user)) -> UserPrivate:
    return _build_user_private(user)


@router.patch("/me", response_model=UserPrivate)
async def update_me(payload: UpdateProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserPrivate:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return _build_user_private(user)


@router.post("/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(payload.new_password)
    db.execute(RefreshToken.__table__.update().where(RefreshToken.user_id == user.id).values(revoked=True))
    db.commit()
    return Response(status_code=204)