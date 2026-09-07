"""Catalog models: categories, makes, models, locations."""
from __future__ import annotations
from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vehicle category: Sedan, SUV, etc."""
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cars: Mapped[List["Car"]] = relationship("Car", back_populates="category")


class Location(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Hierarchical location: country > city > district."""
    __tablename__ = "locations"
    __table_args__ = (Index("ix_locations_country_city", "country", "city"),)

    country: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    district: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    cars: Mapped[List["Car"]] = relationship("Car", back_populates="location")


class Make(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vehicle make (manufacturer)."""
    __tablename__ = "makes"

    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    models: Mapped[List["Model"]] = relationship("Model", back_populates="make", cascade="all, delete-orphan")
    cars: Mapped[List["Car"]] = relationship("Car", back_populates="make")


class Model(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vehicle model belonging to a make."""
    __tablename__ = "models"
    __table_args__ = (
        UniqueConstraint("make_id", "slug", name="uq_make_model_slug"),
        Index("ix_models_make_id", "make_id"),
    )

    make_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("makes.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    body_type: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    make: Mapped["Make"] = relationship("Make", back_populates="models")
    cars: Mapped[List["Car"]] = relationship("Car", back_populates="model")