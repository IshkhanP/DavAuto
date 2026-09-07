"""Messaging API: conversations and messages."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.messaging import Conversation, ConversationParticipant, Message
from app.models.car import Car
from app.models.user import User
from app.models.enums import NotificationType
from app.permissions.rbac import get_current_user
from app.schemas.messaging import (
    ConversationCreate, ConversationOut, MessageCreate, MessageOut,
    ConversationParticipantOut,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/conversations", tags=["messaging"])


def _is_participant(conv: Conversation, user_id: uuid_module.UUID) -> bool:
    return any(p.user_id == user_id for p in conv.participants)


@router.post("", response_model=ConversationOut, status_code=201)
def create_or_get_conversation(
    payload: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipient = db.get(User, uuid_module.UUID(payload.recipient_id))
    if not recipient or recipient.id == user.id:
        raise HTTPException(status_code=400, detail="Invalid recipient")

    car = None
    if payload.car_id:
        car = db.get(Car, uuid_module.UUID(payload.car_id))
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

    # Try to find an existing conversation between these users for this car
    stmt = (
        select(Conversation)
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
        .where(Conversation.car_id == (car.id if car else None))
        .where(ConversationParticipant.user_id.in_([user.id, recipient.id]))
        .group_by(Conversation.id)
        .having(func.count(ConversationParticipant.id) == 2)
    )
    existing = db.execute(stmt).scalars().first()
    if existing:
        # check both participants are part of it
        participants = {p.user.id for p in existing.participants}
        if user.id in participants and recipient.id in participants:
            return _build_conversation_out(db, existing, user.id)

    conv = Conversation(
        car_id=car.id if car else None,
        subject=payload.subject,
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    db.flush()

    db.add(ConversationParticipant(conversation_id=conv.id, user_id=user.id))
    db.add(ConversationParticipant(conversation_id=conv.id, user_id=recipient.id))

    db.add(Message(
        conversation_id=conv.id,
        sender_id=user.id,
        body=payload.initial_message,
    ))

    create_notification(
        db,
        user_id=recipient.id,
        type=NotificationType.NEW_MESSAGE.value,
        title=f"New message from {user.full_name}",
        body=payload.initial_message[:120],
        data={"conversation_id": str(conv.id), "car_id": str(car.id) if car else None},
    )

    db.commit()
    db.refresh(conv)
    return _build_conversation_out(db, conv, user.id)


@router.get("", response_model=List[ConversationOut])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = (
        select(Conversation)
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
        .where(ConversationParticipant.user_id == user.id)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages),
        )
        .order_by(desc(Conversation.last_message_at))
    )
    rows = db.execute(stmt).scalars().unique().all()
    return [_build_conversation_out(db, c, user.id) for c in rows]


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = _load_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not _is_participant(conv, user.id):
        raise HTTPException(status_code=403, detail="Not a participant")
    return _build_conversation_out(db, conv, user.id)


@router.get("/{conversation_id}/messages", response_model=List[MessageOut])
def list_messages(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    conv = _load_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not _is_participant(conv, user.id):
        raise HTTPException(status_code=403, detail="Not a participant")

    rows = db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
        .offset((page - 1) * limit).limit(limit)
    ).scalars().all()
    return [MessageOut.model_validate(m) for m in rows]


@router.post("/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _load_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    me = next((p for p in conv.participants if p.user_id == user.id), None)
    if not me or me.is_blocked:
        raise HTTPException(status_code=403, detail="Not allowed")

    msg = Message(conversation_id=conv.id, sender_id=user.id, body=payload.body)
    db.add(msg)

    conv.last_message_at = datetime.now(timezone.utc)

    for p in conv.participants:
        if p.user_id == user.id:
            p.unread_count = 0
            p.last_read_at = datetime.now(timezone.utc)
        else:
            p.unread_count = (p.unread_count or 0) + 1
            create_notification(
                db,
                user_id=p.user_id,
                type=NotificationType.NEW_MESSAGE.value,
                title=f"New message from {user.full_name}",
                body=payload.body[:120],
                data={"conversation_id": str(conv.id)},
            )

    db.commit()
    db.refresh(msg)
    return MessageOut.model_validate(msg)


@router.post("/{conversation_id}/read", status_code=204)
def mark_read(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = _load_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    me = next((p for p in conv.participants if p.user_id == user.id), None)
    if not me:
        raise HTTPException(status_code=403, detail="Not allowed")
    me.unread_count = 0
    me.last_read_at = datetime.now(timezone.utc)
    db.execute(
        Message.__table__.update()
        .where(and_(Message.conversation_id == conv.id, Message.sender_id != user.id, Message.is_read == False))  # noqa: E712
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    db.commit()
    return None


@router.post("/{conversation_id}/block", status_code=204)
def block_user(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = _load_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    me = next((p for p in conv.participants if p.user_id == user.id), None)
    other = next((p for p in conv.participants if p.user_id != user.id), None)
    if not me or not other:
        raise HTTPException(status_code=403, detail="Not allowed")
    other.is_blocked = True
    db.commit()
    return None


def _load_conversation(db: Session, conv_id: str) -> Optional[Conversation]:
    return db.execute(
        select(Conversation)
        .where(Conversation.id == uuid_module.UUID(conv_id))
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages),
        )
    ).scalar_one_or_none()


def _build_conversation_out(db: Session, conv: Conversation, user_id: uuid_module.UUID) -> ConversationOut:
    me = next((p for p in conv.participants if p.user_id == user_id), None)
    participants = []
    for p in conv.participants:
        u = p.user
        participants.append(ConversationParticipantOut(
            user_id=str(u.id),
            full_name=u.full_name,
            avatar_url=u.avatar_url,
            unread_count=p.unread_count,
            last_read_at=p.last_read_at,
        ))
    last_msg = max(conv.messages, key=lambda m: m.created_at, default=None)
    return ConversationOut(
        id=str(conv.id),
        car_id=str(conv.car_id) if conv.car_id else None,
        subject=conv.subject,
        last_message_at=conv.last_message_at,
        is_active=conv.is_active,
        participants=participants,
        last_message=MessageOut.model_validate(last_msg) if last_msg else None,
        unread_count=me.unread_count if me else 0,
        created_at=conv.created_at,
    )