"""Messaging models: conversations and messages."""
from __future__ import annotations
from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, func, Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Conversation between two or more participants about a car."""
    __tablename__ = "conversations"

    car_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=True, index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    car: Mapped[Optional["Car"]] = relationship("Car")
    participants: Mapped[List["ConversationParticipant"]] = relationship(
        "ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class ConversationParticipant(Base):
    """A user taking part in a conversation."""
    __tablename__ = "conversation_participants"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_count: Mapped[int] = mapped_column(default=0, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="participants")
    user: Mapped["User"] = relationship("User")


class Message(Base, UUIDPrimaryKeyMixin):
    """A single chat message."""
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conv_created", "conversation_id", "created_at"),)

    conversation_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    sender: Mapped["User"] = relationship("User")


class Notification(Base, UUIDPrimaryKeyMixin):
    """User-scoped notification."""
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notif_user_unread", "user_id", "is_read"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(postgresql.JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)