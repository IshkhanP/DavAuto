"""Messaging, favorites, notifications, dealer, promotion schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import ORMBase


# ---------- Favorites ----------
class FavoriteToggleResponse(BaseModel):
    favorited: bool
    favorites_count: int


# ---------- Messaging ----------
class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(ORMBase):
    id: str
    conversation_id: str
    sender_id: str
    body: str
    is_read: bool
    is_system: bool
    created_at: datetime


class ConversationCreate(BaseModel):
    car_id: Optional[str] = None
    recipient_id: str
    subject: Optional[str] = Field(default=None, max_length=200)
    initial_message: str = Field(min_length=1, max_length=4000)


class ConversationParticipantOut(ORMBase):
    user_id: str
    full_name: str
    avatar_url: Optional[str] = None
    unread_count: int
    last_read_at: Optional[datetime] = None


class ConversationOut(ORMBase):
    id: str
    car_id: Optional[str] = None
    subject: Optional[str] = None
    last_message_at: Optional[datetime] = None
    is_active: bool
    participants: List[ConversationParticipantOut]
    last_message: Optional[MessageOut] = None
    unread_count: int
    created_at: datetime


# ---------- Notifications ----------
class NotificationOut(ORMBase):
    id: str
    type: str
    title: str
    body: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class UnreadCountOut(BaseModel):
    unread: int


# ---------- Dealers ----------
class DealerCreate(BaseModel):
    business_name: str = Field(min_length=2, max_length=160)
    slug: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    cover_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    working_hours: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


class DealerUpdate(DealerCreate):
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class DealerOut(ORMBase):
    id: str
    owner_id: str
    business_name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    cover_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    working_hours: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DealerEmployeeAdd(BaseModel):
    user_id: str
    position: Optional[str] = None


# ---------- Reports ----------
class ReportCreate(BaseModel):
    car_id: Optional[str] = None
    reported_user_id: Optional[str] = None
    reason: str
    description: Optional[str] = None


class ReportResolveRequest(BaseModel):
    status: str  # RESOLVED | REJECTED
    resolution_notes: Optional[str] = None
    action: Optional[str] = None  # hide_listing, suspend_user, ban_user, none


class ReportOut(ORMBase):
    id: str
    reporter_id: str
    car_id: Optional[str] = None
    reported_user_id: Optional[str] = None
    reason: str
    description: Optional[str] = None
    status: str
    resolved_by_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


# ---------- Promotions ----------
class PromotionPackageCreate(BaseModel):
    name: str
    slug: str
    promotion_type: str
    description: Optional[str] = None
    price: float
    currency: str = "USD"
    duration_days: int = Field(ge=1)
    max_active_per_user: int = 10
    is_active: bool = True
    display_order: int = 0


class PromotionPackageUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    duration_days: Optional[int] = None
    max_active_per_user: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class PromotionPackageOut(ORMBase):
    id: str
    name: str
    slug: str
    promotion_type: str
    description: Optional[str] = None
    price: float
    currency: str
    duration_days: int
    max_active_per_user: int
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class PurchasePromotionRequest(BaseModel):
    package_id: str
    car_id: str
    payment_provider: Optional[str] = None  # placeholder for future


class UserPromotionOut(ORMBase):
    id: str
    user_id: str
    car_id: str
    promotion_type: str
    starts_at: datetime
    expires_at: datetime
    is_active: bool


# ---------- Payments ----------
class PaymentOut(ORMBase):
    id: str
    user_id: str
    promotion_id: Optional[str] = None
    package_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    provider: Optional[str] = None
    provider_payment_id: Optional[str] = None
    description: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


# ---------- Reviews ----------
class ReviewCreate(BaseModel):
    dealer_id: Optional[str] = None
    seller_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = None
    body: Optional[str] = None


class ReviewOut(ORMBase):
    id: str
    reviewer_id: str
    dealer_id: Optional[str] = None
    seller_id: Optional[str] = None
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    is_approved: bool
    created_at: datetime


# ---------- Settings ----------
class SiteSettingOut(ORMBase):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None
    updated_at: datetime


class SiteSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None