"""Super-admin endpoints.

Only callers that the database identifies as having the SUPER_ADMIN role
can hit any of these routes.  Frontend claims are NEVER trusted — we look
the role up via the JWT-derived User record.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole, Role, Permission, RolePermission, RefreshToken
from app.models.car import Car
from app.models.catalog import Category, Make, Model as CarModel, Location
from app.models.dealer import PromotionPackage, AuditLog, SiteSetting
from app.models.enums import AuditAction
from app.permissions.rbac import (
    get_current_user, is_super_admin,
)
from app.schemas.admin import (
    AdminCreateRequest, AdminUpdateRequest, AdminOut, AdminUserUpdate,
    RoleCreate, RoleUpdate, RoleOut, PermissionOut, AuditLogOut,
)
from app.schemas.messaging import SiteSettingOut, SiteSettingUpdate
from app.schemas.catalog import CategoryCreate, CategoryUpdate, CategoryOut, MakeCreate, MakeUpdate, MakeOut, ModelCreate, ModelUpdate, ModelOut, LocationCreate, LocationUpdate, LocationOut
from app.schemas.messaging import PromotionPackageCreate, PromotionPackageUpdate, PromotionPackageOut
from app.schemas.common import PaginatedResponse, orm_to_dict
from app.utils.slug import slugify
from app.services.audit import log_action

router = APIRouter(prefix="/super-admin", tags=["super-admin"])


def _require_super_admin(user: User) -> None:
    if not is_super_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-admin access required")


# ---- Admins ----
@router.get("/admins", response_model=PaginatedResponse[AdminOut])
def list_admins(
    page: int = 1, limit: int = 24,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)

    # NOTE: this endpoint used to filter to only admin-tier roles (ADMIN,
    # MODERATOR, LISTING_MANAGER, etc.), which meant plain USER accounts
    # never showed up here at all — even though the frontend
    # (SuperAdminAdminsPage) treats this as "every user in the system" and
    # computes counts/filters (Standard users, Dealers, ...) from it. That
    # mismatch was the root cause of the Users screen — and any counts
    # derived from it — looking empty or wrong. It now returns every user,
    # super admins included, with an explicit `is_super_admin` flag so the
    # frontend can still protect super-admin accounts from deletion/role
    # changes without needing to guess from the roles list.
    stmt = select(User).order_by(User.created_at.desc())
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    rows = db.execute(stmt.offset((page - 1) * limit).limit(limit)).scalars().unique().all()
    out = []
    for u in rows:
        role_slugs = [r.role.slug for r in u.roles]
        out.append(AdminOut(
            id=str(u.id), email=u.email, full_name=u.full_name, phone=u.phone,
            status=u.status, is_email_verified=u.is_email_verified,
            last_login_at=u.last_login_at, last_login_ip=u.last_login_ip,
            roles=role_slugs,
            created_at=u.created_at,
            is_super_admin=("SUPER_ADMIN" in role_slugs),
        ))
    return PaginatedResponse[AdminOut].build(out, page, limit, total)


@router.post("/admins", response_model=AdminOut, status_code=201)
def create_admin(
    payload: AdminCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)

    if db.execute(select(User).where(User.email == payload.email.lower())).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    role = db.get(Role, uuid_module.UUID(payload.role_id))
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")
    if role.slug == "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Cannot grant SUPER_ADMIN via this endpoint")

    new_user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
        status="ACTIVE",
        is_email_verified=True,
    )
    new_user.roles.append(UserRole(role=role))
    db.add(new_user)
    db.flush()

    log_action(db, action=AuditAction.SUPER_ADMIN_CREATED_ADMIN.value, user_id=user.id, request=request,
               resource_type="user", resource_id=str(new_user.id),
               metadata={"role": role.slug, "email": new_user.email})

    db.commit()
    db.refresh(new_user)
    return AdminOut(
        id=str(new_user.id), email=new_user.email, full_name=new_user.full_name, phone=new_user.phone,
        status=new_user.status, is_email_verified=new_user.is_email_verified,
        last_login_at=new_user.last_login_at, last_login_ip=new_user.last_login_ip,
        roles=[r.role.slug for r in new_user.roles], created_at=new_user.created_at,
        is_super_admin=False,
    )


@router.patch("/admins/{user_id}", response_model=AdminOut)
def update_admin(
    user_id: str,
    payload: AdminUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    target = db.get(User, uuid_module.UUID(user_id))
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account here")

    data = payload.model_dump(exclude_unset=True)
    if "role_id" in data:
        new_role = db.get(Role, uuid_module.UUID(data["role_id"]))
        if not new_role:
            raise HTTPException(status_code=400, detail="Invalid role")
        if new_role.slug == "SUPER_ADMIN":
            raise HTTPException(status_code=403, detail="Cannot grant SUPER_ADMIN")
        target.roles.clear()
        target.roles.append(UserRole(role=new_role))
        log_action(db, action=AuditAction.SUPER_ADMIN_CHANGED_PERMISSION.value, user_id=user.id, request=request,
                   resource_type="user", resource_id=user_id,
                   metadata={"new_role": new_role.slug})

    for f in ("full_name", "phone", "status"):
        if f in data:
            setattr(target, f, data[f])

    if data.get("status") == "SUSPENDED":
        log_action(db, action=AuditAction.SUPER_ADMIN_SUSPENDED_ADMIN.value, user_id=user.id, request=request,
                   resource_type="user", resource_id=user_id)
        db.execute(RefreshToken.__table__.update().where(RefreshToken.user_id == target.id).values(revoked=True))

    db.commit()
    db.refresh(target)
    role_slugs = [r.role.slug for r in target.roles]
    return AdminOut(
        id=str(target.id), email=target.email, full_name=target.full_name, phone=target.phone,
        status=target.status, is_email_verified=target.is_email_verified,
        last_login_at=target.last_login_at, last_login_ip=target.last_login_ip,
        roles=role_slugs, created_at=target.created_at,
        is_super_admin=("SUPER_ADMIN" in role_slugs),
    )


@router.delete("/admins/{user_id}", status_code=204)
def delete_admin(
    user_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    target = db.get(User, uuid_module.UUID(user_id))
    if not target:
        raise HTTPException(status_code=404, detail="Admin not found")
    if target.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if any(r.role.slug == "SUPER_ADMIN" for r in target.roles):
        raise HTTPException(status_code=403, detail="Cannot delete a SUPER_ADMIN via this endpoint")

    log_action(db, action=AuditAction.SUPER_ADMIN_DELETED_ADMIN.value, user_id=user.id, request=request,
               resource_type="user", resource_id=user_id)
    db.delete(target)
    db.commit()
    return None


# ---- Roles & Permissions ----
@router.get("/permissions", response_model=List[PermissionOut])
def list_permissions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    rows = db.execute(select(Permission).order_by(Permission.category, Permission.code)).scalars().all()
    return [PermissionOut.model_validate(orm_to_dict(p)) for p in rows]


@router.get("/roles", response_model=PaginatedResponse[RoleOut])
def list_roles(
    page: int = 1, limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    total = db.execute(select(func.count(Role.id))).scalar() or 0
    rows = db.execute(
        select(Role)
        .order_by(Role.is_system.desc(), Role.name)
        .offset((page - 1) * limit).limit(limit)
    ).scalars().unique().all()
    items = []
    for r in rows:
        perms = db.execute(select(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role_id == r.id)).scalars().all()
        items.append(RoleOut(
            id=str(r.id), name=r.name, slug=r.slug, description=r.description,
            is_system=r.is_system, is_default=r.is_default,
            permissions=[PermissionOut.model_validate(orm_to_dict(p)) for p in perms],
            created_at=r.created_at, updated_at=r.updated_at,
        ))
    return PaginatedResponse[RoleOut].build(items, page, limit, total)


@router.post("/roles", response_model=RoleOut, status_code=201)
def create_role(
    payload: RoleCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    if db.execute(select(Role).where(Role.slug == payload.slug)).scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role slug already exists")

    role = Role(name=payload.name, slug=payload.slug, description=payload.description, is_system=False)
    db.add(role)
    db.flush()

    for pid in payload.permission_ids or []:
        perm = db.get(Permission, uuid_module.UUID(pid))
        if perm:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    log_action(db, action=AuditAction.SUPER_ADMIN_CREATED_ROLE.value, user_id=user.id, request=request,
               resource_type="role", resource_id=str(role.id),
               metadata={"slug": role.slug, "permissions": payload.permission_ids})
    db.commit()

    perms = db.execute(select(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role_id == role.id)).scalars().all()
    return RoleOut(
        id=str(role.id), name=role.name, slug=role.slug, description=role.description,
        is_system=role.is_system, is_default=role.is_default,
        permissions=[PermissionOut.model_validate(p) for p in perms],
        created_at=role.created_at, updated_at=role.updated_at,
    )


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: str,
    payload: RoleUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    role = db.get(Role, uuid_module.UUID(role_id))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.slug == "SUPER_ADMIN":
        raise HTTPException(status_code=400, detail="Cannot modify SUPER_ADMIN role")

    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description

    if payload.permission_ids is not None:
        db.execute(RolePermission.__table__.delete().where(RolePermission.role_id == role.id))
        for pid in payload.permission_ids:
            perm = db.get(Permission, uuid_module.UUID(pid))
            if perm:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        log_action(db, action=AuditAction.SUPER_ADMIN_CHANGED_PERMISSION.value, user_id=user.id, request=request,
                   resource_type="role", resource_id=str(role.id),
                   metadata={"permissions": payload.permission_ids})

    log_action(db, action=AuditAction.SUPER_ADMIN_UPDATED_ROLE.value, user_id=user.id, request=request,
               resource_type="role", resource_id=str(role.id))
    db.commit()

    perms = db.execute(select(Permission).join(RolePermission, RolePermission.permission_id == Permission.id).where(RolePermission.role_id == role.id)).scalars().all()
    return RoleOut(
        id=str(role.id), name=role.name, slug=role.slug, description=role.description,
        is_system=role.is_system, is_default=role.is_default,
        permissions=[PermissionOut.model_validate(p) for p in perms],
        created_at=role.created_at, updated_at=role.updated_at,
    )


@router.delete("/roles/{role_id}", status_code=204)
def delete_role(
    role_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    role = db.get(Role, uuid_module.UUID(role_id))
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    log_action(db, action=AuditAction.SUPER_ADMIN_DELETED_ROLE.value, user_id=user.id, request=request,
               resource_type="role", resource_id=str(role.id))
    db.delete(role)
    db.commit()
    return None


# ---- Categories / Makes / Models / Locations ----
@router.get("/categories", response_model=List[CategoryOut])
def sa_list_categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    return [
        CategoryOut.model_validate(orm_to_dict(c))
        for c in db.execute(select(Category).order_by(Category.display_order, Category.name)).scalars().all()
    ]


@router.post("/categories", response_model=CategoryOut, status_code=201)
def sa_create_category(
    payload: CategoryCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    cat = Category(**payload.model_dump())
    db.add(cat)
    log_action(db, action=AuditAction.SUPER_ADMIN_UPDATED_SETTINGS.value, user_id=user.id, request=request,
               resource_type="category", metadata={"name": cat.name})
    db.commit()
    db.refresh(cat)
    return cat


@router.patch("/categories/{cat_id}", response_model=CategoryOut)
def sa_update_category(cat_id: str, payload: CategoryUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    cat = db.get(Category, uuid_module.UUID(cat_id))
    if not cat:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    return cat


@router.delete("/categories/{cat_id}", status_code=204)
def sa_delete_category(cat_id: str, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    cat = db.get(Category, uuid_module.UUID(cat_id))
    if not cat:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(cat)
    db.commit()
    return None


@router.get("/makes", response_model=List[MakeOut])
def sa_list_makes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    return [
        MakeOut.model_validate(orm_to_dict(m))
        for m in db.execute(select(Make).order_by(Make.name)).scalars().all()
    ]


@router.post("/makes", response_model=MakeOut, status_code=201)
def sa_create_make(payload: MakeCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    make = Make(**payload.model_dump())
    db.add(make)
    db.commit()
    db.refresh(make)
    return make


@router.patch("/makes/{make_id}", response_model=MakeOut)
def sa_update_make(make_id: str, payload: MakeUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    make = db.get(Make, uuid_module.UUID(make_id))
    if not make:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(make, k, v)
    db.commit()
    return make


@router.delete("/makes/{make_id}", status_code=204)
def sa_delete_make(make_id: str, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    make = db.get(Make, uuid_module.UUID(make_id))
    if not make:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(make)
    db.commit()
    return None


@router.post("/makes/{make_id}/models", response_model=ModelOut, status_code=201)
def sa_create_model(make_id: str, payload: ModelCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    make = db.get(Make, uuid_module.UUID(make_id))
    if not make:
        raise HTTPException(status_code=404, detail="Make not found")
    model = CarModel(make_id=make.id, name=payload.name, slug=payload.slug, body_type=payload.body_type, is_active=payload.is_active)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.patch("/models/{model_id}", response_model=ModelOut)
def sa_update_model(model_id: str, payload: ModelUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    model = db.get(CarModel, uuid_module.UUID(model_id))
    if not model:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(model, k, v)
    db.commit()
    return model


@router.delete("/models/{model_id}", status_code=204)
def sa_delete_model(model_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    model = db.get(CarModel, uuid_module.UUID(model_id))
    if not model:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(model)
    db.commit()
    return None


@router.get("/locations", response_model=List[LocationOut])
def sa_list_locations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    return [
        LocationOut.model_validate(orm_to_dict(l))
        for l in db.execute(select(Location).order_by(Location.country, Location.city)).scalars().all()
    ]


@router.post("/locations", response_model=LocationOut, status_code=201)
def sa_create_location(payload: LocationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    loc = Location(**payload.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


@router.patch("/locations/{loc_id}", response_model=LocationOut)
def sa_update_location(loc_id: str, payload: LocationUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    loc = db.get(Location, uuid_module.UUID(loc_id))
    if not loc:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(loc, k, v)
    db.commit()
    return loc


@router.delete("/locations/{loc_id}", status_code=204)
def sa_delete_location(loc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    loc = db.get(Location, uuid_module.UUID(loc_id))
    if not loc:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(loc)
    db.commit()
    return None


# ---- Promotion Packages ----
@router.get("/promotion-packages", response_model=List[PromotionPackageOut])
def sa_list_packages(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    return [
        PromotionPackageOut.model_validate(orm_to_dict(p))
        for p in db.execute(select(PromotionPackage).order_by(PromotionPackage.display_order)).scalars().all()
    ]


@router.post("/promotion-packages", response_model=PromotionPackageOut, status_code=201)
def sa_create_package(payload: PromotionPackageCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    pkg = PromotionPackage(**payload.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.patch("/promotion-packages/{pkg_id}", response_model=PromotionPackageOut)
def sa_update_package(pkg_id: str, payload: PromotionPackageUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    pkg = db.get(PromotionPackage, uuid_module.UUID(pkg_id))
    if not pkg:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(pkg, k, v)
    db.commit()
    return pkg


@router.delete("/promotion-packages/{pkg_id}", status_code=204)
def sa_delete_package(pkg_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    pkg = db.get(PromotionPackage, uuid_module.UUID(pkg_id))
    if not pkg:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(pkg)
    db.commit()
    return None


# ---- Site Settings ----
@router.get("/settings", response_model=List[SiteSettingOut])
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_super_admin(user)
    return [
        SiteSettingOut.model_validate(orm_to_dict(s))
        for s in db.execute(select(SiteSetting).order_by(SiteSetting.key)).scalars().all()
    ]


@router.put("/settings/{key}", response_model=SiteSettingOut)
def update_setting(
    key: str,
    payload: SiteSettingUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    s = db.get(SiteSetting, key)
    if not s:
        s = SiteSetting(key=key, value=payload.value, description=payload.description)
        db.add(s)
    else:
        s.value = payload.value
        if payload.description is not None:
            s.description = payload.description
    log_action(db, action=AuditAction.SUPER_ADMIN_UPDATED_SETTINGS.value, user_id=user.id, request=request,
               resource_type="setting", resource_id=key, metadata={"value": payload.value})
    db.commit()
    db.refresh(s)
    return s


# ---- Audit Logs ----
@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogOut])
def list_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_super_admin(user)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if user_id:
        stmt = stmt.where(AuditLog.user_id == uuid_module.UUID(user_id))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    rows = db.execute(stmt.offset((page - 1) * limit).limit(limit)).scalars().all()
    return PaginatedResponse[AuditLogOut].build(
        [AuditLogOut.model_validate(orm_to_dict(r)) for r in rows], page, limit, total
    )
