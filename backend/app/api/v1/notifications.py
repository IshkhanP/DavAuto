"""Notification API."""
from __future__ import annotations
from typing import Optional
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.messaging import Notification
from app.models.user import User
from app.permissions.rbac import get_current_user
from app.schemas.common import PaginatedResponse
from app.schemas.messaging import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationOut])
def list_notifications(
    page: int = 1,
    limit: int = 30,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
    ).scalar() or 0

    rows = db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * limit).limit(limit)
    ).scalars().all()

    items = [NotificationOut.model_validate(n) for n in rows]
    return PaginatedResponse[NotificationOut].build(items, page, limit, total)


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id, Notification.is_read == False  # noqa: E712
        )
    ).scalar() or 0
    return UnreadCountOut(unread=count)


@router.post("/{notification_id}/read", status_code=204)
def mark_read(notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, uuid_module.UUID(notification_id))
    if not n or n.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not n.is_read:
        n.is_read = True
        n.read_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        db.commit()
    return None


@router.post("/read-all", status_code=204)
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == user.id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))
    )
    db.commit()
    return None