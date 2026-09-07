"""Audit logging helper."""
from __future__ import annotations
from typing import Optional, Dict, Any
import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.dealer import AuditLog


def log_action(
    db: Session,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    if request is not None:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.flush()
    return entry