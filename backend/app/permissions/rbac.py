"""RBAC FastAPI dependencies.

These dependencies MUST be applied to every protected endpoint.  Never
rely on frontend claims — these always derive the user's identity from the
JWT and look up roles / permissions in the database.
"""
from __future__ import annotations
from typing import Iterable, List, Optional
import uuid as uuid_module

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.user import User, UserRole, Role, RolePermission, Permission


def _build_user_permissions(user: User) -> List[str]:
    seen = set()
    for ur in user.roles:
        for rp in ur.role.permissions:
            seen.add(rp.permission.code)
    return list(seen)


def _ensure_user_loaded(user: User) -> User:
    # ``User.roles`` is configured with ``lazy="selectin"`` so it should be
    # populated already.  This helper exists as a safety net for cases where
    # the relationship might not be loaded.
    if not hasattr(user, "roles") or user.roles is None:
        return user
    return user


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the JWT in the Authorization header.

    Frontend MUST send ``Authorization: Bearer <access_token>``.  Trust is
    never placed in any frontend-supplied role or permission claims.
    """
    auth_header = request.headers.get("Authorization") or ""
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ", 1)[1].strip()

    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        user_id = uuid_module.UUID(sub)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission)
        )
    )
    user = db.execute(stmt).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.status in ("BANNED", "SUSPENDED"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Account {user.status.lower()}")

    return user


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optional auth: returns the user if the token is valid, otherwise None."""
    auth_header = request.headers.get("Authorization") or ""
    if not auth_header.lower().startswith("bearer "):
        return None
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


def require_roles(*role_slugs: str):
    """Dependency factory: user must have at least one of the given role slugs."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        user_role_slugs = {r.role.slug for r in user.roles}
        if not user_role_slugs.intersection(role_slugs):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return user

    return _checker


def require_permission(*permission_codes: str):
    """Dependency factory: user must have ALL of the given permission codes."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        user_perms = set(_build_user_permissions(user))
        missing = set(permission_codes) - user_perms
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {sorted(missing)[0]}",
            )
        return user

    return _checker


def require_any_permission(*permission_codes: str):
    """Dependency factory: user must have at least one of the given permissions."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        user_perms = set(_build_user_permissions(user))
        if not user_perms.intersection(permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _checker


def has_role(user: User, role_slug: str) -> bool:
    return any(r.role.slug == role_slug for r in user.roles)


def is_super_admin(user: User) -> bool:
    return has_role(user, "SUPER_ADMIN")


def is_admin_or_above(user: User) -> bool:
    return any(has_role(user, r) for r in ("SUPER_ADMIN", "ADMIN"))


def has_permission(user: User, code: str) -> bool:
    return code in _build_user_permissions(user)


def has_any_permission(user: User, codes: Iterable[str]) -> bool:
    user_perms = set(_build_user_permissions(user))
    return bool(user_perms.intersection(codes))