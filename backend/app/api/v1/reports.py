"""Reports endpoints."""
from __future__ import annotations
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dealer import Report
from app.models.user import User
from app.models.car import Car
from app.models.enums import ReportStatus, CarStatus, NotificationType
from app.permissions.rbac import get_current_user
from app.schemas.messaging import ReportCreate, ReportOut, ReportResolveRequest
from app.services.notifications import create_notification

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.car_id and not payload.reported_user_id:
        raise HTTPException(status_code=400, detail="car_id or reported_user_id required")
    if payload.car_id:
        car = db.get(Car, uuid_module.UUID(payload.car_id))
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

    report = Report(
        reporter_id=user.id,
        car_id=uuid_module.UUID(payload.car_id) if payload.car_id else None,
        reported_user_id=uuid_module.UUID(payload.reported_user_id) if payload.reported_user_id else None,
        reason=payload.reason,
        description=payload.description,
        status=ReportStatus.PENDING.value,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/mine", response_model=list[ReportOut])
def my_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Report).where(Report.reporter_id == user.id).order_by(Report.created_at.desc())
    ).scalars().all()
    return [ReportOut.model_validate(r) for r in rows]