"""Dealer, report, promotion and audit models."""
from __future__ import annotations
from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Boolean, DateTime, Text, Integer, func, Index, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Dealer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A dealer / business entity."""
    __tablename__ = "dealers"

    owner_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    working_hours: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    social_links: Mapped[Optional[dict]] = mapped_column(postgresql.JSONB, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employees: Mapped[List["DealerEmployee"]] = relationship("DealerEmployee", back_populates="dealer", cascade="all, delete-orphan")
    cars: Mapped[List["Car"]] = relationship("Car", back_populates="dealer")


class DealerEmployee(Base):
    """A user working for a dealer."""
    __tablename__ = "dealer_employees"
    __table_args__ = (UniqueConstraint("dealer_id", "user_id", name="uq_dealer_user"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("dealers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="employees")
    user: Mapped["User"] = relationship("User")


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user-submitted report against a listing or user."""
    __tablename__ = "reports"

    reporter_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=True, index=True)
    reported_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PromotionPackage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configurable promotion offering (configurable by Super Admin)."""
    __tablename__ = "promotion_packages"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    promotion_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_active_per_user: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class UserPromotion(Base, UUIDPrimaryKeyMixin):
    """An active promotion tied to a user and a car."""
    __tablename__ = "user_promotions"
    __table_args__ = (Index("ix_user_promotions_active", "car_id", "expires_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("promotion_packages.id", ondelete="RESTRICT"), nullable=False)
    promotion_type: Mapped[str] = mapped_column(String(40), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Payment record (cards handled by external provider)."""
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    promotion_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("user_promotions.id", ondelete="SET NULL"), nullable=True)
    package_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("promotion_packages.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user review of a dealer or seller."""
    __tablename__ = "reviews"

    reviewer_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dealer_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("dealers.id", ondelete="CASCADE"), nullable=True, index=True)
    seller_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Append-only audit log of moderation / super-admin actions."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_user", "user_id"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
        Index("ix_audit_created", "created_at"),
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(postgresql.JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SiteSetting(Base):
    """System-wide configuration key/value store."""
    __tablename__ = "site_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())