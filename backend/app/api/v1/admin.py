"""Admin endpoints: listings moderation, reports, users, dashboard stats.

Every endpoint here is permission-gated.  Frontend must NOT be trusted.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole, Role
from app.models.car import Car
from app.models.dealer import Report, Dealer
from app.models.enums import CarStatus, NotificationType, AuditAction
from app.permissions.rbac import (
    get_current_user,
)
from app.permissions.definitions import PermissionCodes
from app.repositories.car_repository import CarRepository
from app.schemas.car import CarAdminOut
from app.schemas.admin import AdminUserOut, DashboardStats, AdminUserUpdate
from app.schemas.messaging import ReportOut, ReportResolveRequest
from app.schemas.common import PaginatedResponse
from app.services.audit import log_action
from app.services.notifications import create_notification

router = APIRouter(prefix="/admin", tags=["admin"])


# ---- Permission dependency helpers ----
def _require_perm_any(*codes: str):
    """FastAPI dependency: caller must have at least ONE of the given permission codes."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        flat_perms = {
            rp.permission.code
            for ur in user.roles
            for rp in ur.role.permissions
        }
        if not flat_perms.intersection(codes):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _checker


def _require_perm_all(*codes: str):
    """FastAPI dependency: caller must have ALL of the given permission codes."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        flat_perms = {
            rp.permission.code
            for ur in user.roles
            for rp in ur.role.permissions
        }
        missing = set(codes) - flat_perms
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Missing permission: {sorted(missing)[0]}",
            )
        return user
    return _checker


# ---- Dashboard stats ----
@router.get("/stats", response_model=DashboardStats)
def dashboard_stats_endpoint(
    user: User = Depends(_require_perm_any(PermissionCodes.VIEW_USERS, PermissionCodes.VIEW_LISTINGS)),
    db: Session = Depends(get_db),
):
    last_30 = datetime.now(timezone.utc) - timedelta(days=30)

    total_users = db.execute(select(func.count(User.id))).scalar() or 0
    active_users = db.execute(select(func.count(User.id)).where(User.status == "ACTIVE")).scalar() or 0
    total_listings = db.execute(select(func.count(Car.id))).scalar() or 0
    active_listings = db.execute(select(func.count(Car.id)).where(Car.status == "ACTIVE")).scalar() or 0
    pending_listings = db.execute(select(func.count(Car.id)).where(Car.status == "PENDING")).scalar() or 0
    sold_listings = db.execute(select(func.count(Car.id)).where(Car.status == "SOLD")).scalar() or 0
    total_dealers = db.execute(select(func.count(Dealer.id))).scalar() or 0
    total_reports = db.execute(select(func.count(Report.id))).scalar() or 0
    pending_reports = db.execute(select(func.count(Report.id)).where(Report.status == "PENDING")).scalar() or 0

    new_users_last_30d = db.execute(
        select(func.count(User.id)).where(User.created_at >= last_30)
    ).scalar() or 0
    new_listings_last_30d = db.execute(
        select(func.count(Car.id)).where(Car.created_at >= last_30)
    ).scalar() or 0

    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_listings=total_listings,
        active_listings=active_listings,
        pending_listings=pending_listings,
        sold_listings=sold_listings,
        total_dealers=total_dealers,
        total_reports=total_reports,
        pending_reports=pending_reports,
        total_messages=0,  # would need Message model; keeping simple
        total_revenue=0.0,
        new_users_last_30d=new_users_last_30d,
        new_listings_last_30d=new_listings_last_30d,
    )


# ---- Listings moderation ----
@router.get("/listings", response_model=PaginatedResponse[CarAdminOut])
def admin_list_listings(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 24,
    user: User = Depends(_require_perm_all(PermissionCodes.VIEW_LISTINGS)),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    items, total = repo.list_paginated(
        page=page, limit=limit,
        status=status_filter if status_filter else "ACTIVE,DRAFT,PENDING,SOLD,PAUSED,EXPIRED,REJECTED,DELETED",
        q=q,
    )
    cards = []
    from app.api.v1.cars import _to_detail
    for car in items:
        detail = repo.get_with_details(car.id)
        detail_out = _to_detail(detail)
        cards.append(CarAdminOut(
            **detail_out.model_dump(),
            seller_id=str(car.seller_id),
            dealer_id=str(car.dealer_id) if car.dealer_id else None,
            rejection_reason=car.rejection_reason,
        ))
    return PaginatedResponse[CarAdminOut].build(cards, page, limit, total)


@router.patch("/listings/{car_id}/approve", response_model=CarAdminOut)
def approve_listing(
    car_id: str,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.APPROVE_LISTINGS)),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    car.status = CarStatus.ACTIVE.value
    if not car.published_at:
        car.published_at = datetime.now(timezone.utc)
    car.rejection_reason = None
    log_action(db, action=AuditAction.ADMIN_APPROVED_LISTING.value, user_id=user.id, request=request,
               resource_type="car", resource_id=car_id)
    create_notification(db, user_id=car.seller_id, type=NotificationType.LISTING_APPROVED.value,
                        title="Your listing was approved", body=f"{car.make.name if car.make else ''} {car.model.name if car.model else ''}".strip(),
                        data={"car_id": car_id})
    db.commit()
    repo = CarRepository(db)
    detail = repo.get_with_details(car.id)
    from app.api.v1.cars import _to_detail
    return CarAdminOut(**_to_detail(detail).model_dump(),
                       seller_id=str(car.seller_id), dealer_id=str(car.dealer_id) if car.dealer_id else None,
                       rejection_reason=car.rejection_reason)


@router.patch("/listings/{car_id}/reject", response_model=CarAdminOut)
def reject_listing(
    car_id: str,
    payload: dict,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.APPROVE_LISTINGS)),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    car.status = CarStatus.REJECTED.value
    car.rejection_reason = payload.get("reason") if isinstance(payload, dict) else None
    log_action(db, action=AuditAction.ADMIN_REJECTED_LISTING.value, user_id=user.id, request=request,
               resource_type="car", resource_id=car_id,
               metadata={"reason": car.rejection_reason})
    create_notification(db, user_id=car.seller_id, type=NotificationType.LISTING_REJECTED.value,
                        title="Your listing was rejected",
                        body=car.rejection_reason or "Please review and resubmit.",
                        data={"car_id": car_id})
    db.commit()
    repo = CarRepository(db)
    detail = repo.get_with_details(car.id)
    from app.api.v1.cars import _to_detail
    return CarAdminOut(**_to_detail(detail).model_dump(),
                       seller_id=str(car.seller_id), dealer_id=str(car.dealer_id) if car.dealer_id else None,
                       rejection_reason=car.rejection_reason)


@router.patch("/listings/{car_id}/feature", response_model=CarAdminOut)
def feature_listing(
    car_id: str,
    payload: dict,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.MANAGE_LISTINGS)),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    car.is_featured = bool(payload.get("is_featured", True))
    db.commit()
    repo = CarRepository(db)
    detail = repo.get_with_details(car.id)
    from app.api.v1.cars import _to_detail
    return CarAdminOut(**_to_detail(detail).model_dump(),
                       seller_id=str(car.seller_id), dealer_id=str(car.dealer_id) if car.dealer_id else None,
                       rejection_reason=car.rejection_reason)


@router.post("/listings/bulk-action")
def bulk_action(
    payload: dict,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.MANAGE_LISTINGS)),
    db: Session = Depends(get_db),
):
    ids = payload.get("ids") or []
    action = payload.get("action")
    if not ids or not action:
        raise HTTPException(status_code=400, detail="ids and action required")

    affected = 0
    for cid in ids:
        car = db.get(Car, uuid_module.UUID(cid))
        if not car:
            continue
        if action == "approve":
            car.status = CarStatus.ACTIVE.value
        elif action == "reject":
            car.status = CarStatus.REJECTED.value
        elif action == "hide":
            car.status = CarStatus.PAUSED.value
        elif action == "feature":
            car.is_featured = True
        elif action == "unfeature":
            car.is_featured = False
        elif action == "delete":
            db.delete(car)
        else:
            continue
        log_action(db, action=f"ADMIN_BULK_{action.upper()}", user_id=user.id, request=request,
                   resource_type="car", resource_id=cid)
        affected += 1
    db.commit()
    return {"affected": affected}


# ---- Reports ----
@router.get("/reports", response_model=PaginatedResponse[ReportOut])
def list_reports(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = 1,
    limit: int = 24,
    user: User = Depends(_require_perm_all(PermissionCodes.VIEW_REPORTS)),
    db: Session = Depends(get_db),
):
    stmt = select(Report).order_by(Report.created_at.desc())
    if status_filter:
        stmt = stmt.where(Report.status == status_filter)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    rows = db.execute(stmt.offset((page - 1) * limit).limit(limit)).scalars().all()
    return PaginatedResponse[ReportOut].build([ReportOut.model_validate(r) for r in rows], page, limit, total)


@router.post("/reports/{report_id}/resolve")
def resolve_report(
    report_id: str,
    payload: ReportResolveRequest,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.MANAGE_REPORTS)),
    db: Session = Depends(get_db),
):
    report = db.get(Report, uuid_module.UUID(report_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = payload.status
    report.resolution_notes = payload.resolution_notes
    report.resolved_by_id = user.id
    report.resolved_at = datetime.now(timezone.utc)

    action = (payload.action or "").lower()
    if action == "hide_listing" and report.car_id:
        car = db.get(Car, report.car_id)
        if car:
            car.status = CarStatus.PAUSED.value
            log_action(db, action=AuditAction.ADMIN_HID_LISTING.value, user_id=user.id, request=request,
                       resource_type="car", resource_id=str(car.id))
    elif action == "suspend_user" and report.reported_user_id:
        target = db.get(User, report.reported_user_id)
        if target:
            target.status = "SUSPENDED"
            log_action(db, action=AuditAction.ADMIN_SUSPENDED_USER.value, user_id=user.id, request=request,
                       resource_type="user", resource_id=str(target.id))
    elif action == "ban_user" and report.reported_user_id:
        target = db.get(User, report.reported_user_id)
        if target:
            target.status = "BANNED"
            log_action(db, action=AuditAction.ADMIN_BANNED_USER.value, user_id=user.id, request=request,
                       resource_type="user", resource_id=str(target.id))

    log_action(db, action=AuditAction.ADMIN_RESOLVED_REPORT.value, user_id=user.id, request=request,
               resource_type="report", resource_id=report_id,
               metadata={"action": action, "status": payload.status})
    db.commit()
    return {"ok": True}


# ---- Users management ----
@router.get("/users", response_model=PaginatedResponse[AdminUserOut])
def list_users(
    q: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = 1,
    limit: int = 24,
    user: User = Depends(_require_perm_all(PermissionCodes.VIEW_USERS)),
    db: Session = Depends(get_db),
):
    stmt = select(User).order_by(User.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    rows = db.execute(stmt.offset((page - 1) * limit).limit(limit)).scalars().all()
    out = []
    for u in rows:
        cars_count = db.execute(select(func.count(Car.id)).where(Car.seller_id == u.id)).scalar() or 0
        out.append(AdminUserOut(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            status=u.status,
            is_email_verified=u.is_email_verified,
            last_login_at=u.last_login_at,
            last_login_ip=u.last_login_ip,
            roles=[r.role.slug for r in u.roles],
            created_at=u.created_at,
            cars_count=cars_count,
        ))
    return PaginatedResponse[AdminUserOut].build(out, page, limit, total)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user_admin(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    user: User = Depends(_require_perm_all(PermissionCodes.MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    target = db.get(User, uuid_module.UUID(user_id))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    data = payload.model_dump(exclude_unset=True)

    if "role_id" in data:
        new_role = db.get(Role, uuid_module.UUID(data["role_id"]))
        if not new_role:
            raise HTTPException(status_code=400, detail="Invalid role")
        # Admin cannot assign SUPER_ADMIN
        if new_role.slug == "SUPER_ADMIN" and not any(r.role.slug == "SUPER_ADMIN" for r in user.roles):
            raise HTTPException(status_code=403, detail="Only super admin can grant SUPER_ADMIN")
        # Replace roles with the new role (admin only manages regular users)
        target.roles.clear()
        target.roles.append(UserRole(role=new_role))

    for field in ("full_name", "phone", "status", "is_email_verified"):
        if field in data:
            setattr(target, field, data[field])

    if data.get("status") == "SUSPENDED":
        log_action(db, action=AuditAction.ADMIN_SUSPENDED_USER.value, user_id=user.id, request=request,
                   resource_type="user", resource_id=user_id)
    elif data.get("status") == "BANNED":
        log_action(db, action=AuditAction.ADMIN_BANNED_USER.value, user_id=user.id, request=request,
                   resource_type="user", resource_id=user_id)
    elif data.get("status") == "ACTIVE":
        log_action(db, action=AuditAction.ADMIN_RESTORED_USER.value, user_id=user.id, request=request,
                   resource_type="user", resource_id=user_id)

    db.commit()
    db.refresh(target)
    cars_count = db.execute(select(func.count(Car.id)).where(Car.seller_id == target.id)).scalar() or 0
    return AdminUserOut(
        id=str(target.id),
        email=target.email,
        full_name=target.full_name,
        phone=target.phone,
        status=target.status,
        is_email_verified=target.is_email_verified,
        last_login_at=target.last_login_at,
        last_login_ip=target.last_login_ip,
        roles=[r.role.slug for r in target.roles],
        created_at=target.created_at,
        cars_count=cars_count,
    )