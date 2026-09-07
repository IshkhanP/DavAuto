"""Notification service — creates DB notifications for users."""
from __future__ import annotations
from typing import Optional, Dict, Any
import uuid

from sqlalchemy.orm import Session

from app.models.messaging import Notification


def create_notification(
    db: Session,
    *,
    user_id: uuid.UUID,
    type: str,
    title: str,
    body: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data,
    )
    db.add(notification)
    db.flush()
    return notification