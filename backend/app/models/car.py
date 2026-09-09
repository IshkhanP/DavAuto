"""Car / listing models."""
from __future__ import annotations
from typing import List, Optional
import uuid
from datetime import datetime, date

from sqlalchemy import (
    String, Integer, ForeignKey, Boolean, DateTime, Date, Text, Numeric, Index, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Car(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A vehicle listing."""
    __tablename__ = "cars"
    __table_args__ = (
        # Only the multi-column / non-column-level indexes live here.
        Index("ix_cars_fuel_transmission", "fuel_type", "transmission"),
        Index("ix_cars_featured_promoted", "is_featured", "is_promoted"),
        Index("ix_cars_published_at", "published_at"),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dealer_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("dealers.id", ondelete="SET NULL"), nullable=True, index=True)
    make_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("makes.id", ondelete="RESTRICT"), nullable=False, index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("models.id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    mileage: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    vin: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)

    body_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    transmission: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    drive_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)

    engine: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    engine_size: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    horsepower: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    exterior_color: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    interior_color: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    doors: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    condition: Mapped[str] = mapped_column(String(20), nullable=False, default="USED")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT", index=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Contact preferences ---
    # ``phone_country_code`` (e.g. "+1", "+374") is stored separately so the
    # frontend can render an E.164-formatted number when buyers click the
    # contact button.  ``phone_number`` is the local part.
    phone_country_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    # Comma-separated list of preferred contact channels. Allowed values:
    # PHONE, WHATSAPP, VIBER, TELEGRAM, CHAT (chat on site, i.e. the
    # built-in messaging under /dashboard/messages — not a separate app).
    contact_methods: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, default="PHONE,CHAT")

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_promoted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    favorites_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sold_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    seller: Mapped["User"] = relationship("User", back_populates="cars", foreign_keys=[seller_id])
    dealer: Mapped[Optional["Dealer"]] = relationship("Dealer", back_populates="cars")
    make: Mapped["Make"] = relationship("Make", back_populates="cars")
    model: Mapped["Model"] = relationship("Model", back_populates="cars")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="cars")
    location: Mapped[Optional["Location"]] = relationship("Location", back_populates="cars")
    images: Mapped[List["CarImage"]] = relationship("CarImage", back_populates="car", cascade="all, delete-orphan", order_by="CarImage.display_order")
    videos: Mapped[List["CarVideo"]] = relationship("CarVideo", back_populates="car", cascade="all, delete-orphan")
    features: Mapped[List["CarFeature"]] = relationship("CarFeature", back_populates="car", cascade="all, delete-orphan")
    favorites: Mapped[List["Favorite"]] = relationship("Favorite", back_populates="car", cascade="all, delete-orphan")
    daily_views: Mapped[List["CarDailyView"]] = relationship("CarDailyView", back_populates="car", cascade="all, delete-orphan")


class CarImage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vehicle image stored on object storage, URL referenced here."""
    __tablename__ = "car_images"

    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(800), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(800), nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    car: Mapped["Car"] = relationship("Car", back_populates="images")


class CarVideo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vehicle video."""
    __tablename__ = "car_videos"

    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(800), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(800), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    car: Mapped["Car"] = relationship("Car", back_populates="videos")


class CarFeature(Base, UUIDPrimaryKeyMixin):
    """Vehicle feature flag, e.g. 'Sunroof', 'Bluetooth', 'Heated Seats'."""
    __tablename__ = "car_features"

    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    car: Mapped["Car"] = relationship("Car", back_populates="features")


class Favorite(Base):
    """User favorite (a user can favorite a car only once)."""
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "car_id", name="uq_user_car_favorite"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User")
    car: Mapped["Car"] = relationship("Car", back_populates="favorites")


class CarDailyView(Base, UUIDPrimaryKeyMixin):
    """Aggregated per-day view counter for a listing.

    One row per (car_id, view_date), incremented every time the public
    car-detail endpoint records a view (see
    ``CarRepository.increment_views``). This powers the "how many people
    viewed your listing today / this week" statistic sellers see on their
    own listings — the plain ``Car.views_count`` column only tracks the
    lifetime total, with no way to break it down by day.
    """
    __tablename__ = "car_daily_views"
    __table_args__ = (
        UniqueConstraint("car_id", "view_date", name="uq_car_daily_view"),
        Index("ix_car_daily_views_view_date", "view_date"),
    )

    car_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    view_date: Mapped[date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    car: Mapped["Car"] = relationship("Car", back_populates="daily_views")
