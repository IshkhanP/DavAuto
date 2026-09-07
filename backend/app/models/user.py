"""User, role and permission models."""
from __future__ import annotations
from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin


class Permission(Base):
    """Discrete permission that can be granted to a role."""
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="general", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Role(Base):
    """A role bundles a set of permissions and is assigned to a user."""
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    users: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RolePermission(Base):
    """Join table between roles and permissions."""
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped["Role"] = relationship("Role", back_populates="permissions")
    permission: Mapped["Permission"] = relationship("Permission")


class UserRole(Base):
    """Join table between users and roles. A user can have multiple roles."""
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    user: Mapped["User"] = relationship("User", back_populates="roles")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core user record."""
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_lower", func.lower("email")),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    cars: Mapped[List["Car"]] = relationship(
        "Car", back_populates="seller", foreign_keys="Car.seller_id",
        cascade="all, delete-orphan",
    )

    def has_role(self, slug: str) -> bool:
        return any(r.role.slug == slug for r in self.roles)

    def get_role_slugs(self) -> List[str]:
        return [r.role.slug for r in self.roles]


class RefreshToken(Base):
    """Persisted refresh token (allows revocation)."""
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())