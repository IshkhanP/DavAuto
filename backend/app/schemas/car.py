"""Car / listing schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import ORMBase

# Suppress Pydantic's "protected namespace" warning for fields like `model_*`.
# `model_*` is a reserved Pydantic prefix but our domain genuinely uses these
# names for vehicle make/model data, so we opt out of the check globally.
_BASE_CONFIG = ConfigDict(protected_namespaces=(), from_attributes=True)

# Response schemas that use `model_id` / `model_name` (and any other Pydantic
# v2 protected-namespace field) inherit from this so the warning is silenced
# project-wide.  Request schemas that don't have such fields just use BaseModel.
class _SafeResponseBase(ORMBase):
    model_config = ConfigDict(protected_namespaces=())


class CarImageOut(ORMBase):
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    display_order: int
    is_main: bool
    width: Optional[int] = None
    height: Optional[int] = None


class CarVideoOut(ORMBase):
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class CarFeatureOut(ORMBase):
    id: str
    name: str
    value: Optional[str] = None
    category: Optional[str] = None


class SellerSummary(ORMBase):
    id: str
    full_name: str
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    seller_type: str  # USER | DEALER


class CarCardOut(ORMBase):
    """Compact car representation used by listing grids."""
    id: str
    make: str
    model: str
    year: int
    price: float
    currency: str
    mileage: int
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str
    is_featured: bool
    is_promoted: bool
    views_count: int
    favorites_count: int
    main_image: Optional[str] = None
    published_at: Optional[datetime] = None
    seller_type: str


class CarDetailOut(_SafeResponseBase):
    """Full car record returned by GET /cars/:id."""
    id: str
    make_id: str
    model_id: str
    make_name: str
    model_name: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    year: int
    price: float
    currency: str
    mileage: int
    vin: Optional[str] = None

    body_type: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None

    engine: Optional[str] = None
    engine_size: Optional[float] = None
    horsepower: Optional[int] = None

    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    doors: Optional[int] = None
    seats: Optional[int] = None

    description: Optional[str] = None
    condition: str
    status: str
    is_featured: bool
    is_promoted: bool
    is_negotiable: bool
    views_count: int
    favorites_count: int
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    images: List[CarImageOut] = []
    videos: List[CarVideoOut] = []
    features: List[CarFeatureOut] = []

    seller: SellerSummary
    location_display: Optional[str] = None

    # Contact preferences
    phone_country_code: Optional[str] = None
    phone_number: Optional[str] = None
    contact_methods: List[str] = []


class CarCreate(BaseModel):
    model_config = _BASE_CONFIG
    make_id: str
    model_id: str
    category_id: Optional[str] = None
    location_id: Optional[str] = None
    year: int = Field(ge=1900, le=2100)
    price: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=8)
    mileage: int = Field(ge=0)
    vin: Optional[str] = Field(default=None, max_length=40)
    body_type: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    engine: Optional[str] = None
    engine_size: Optional[float] = None
    horsepower: Optional[int] = Field(default=None, ge=0)
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    doors: Optional[int] = Field(default=None, ge=1)
    seats: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    condition: str = Field(default="USED")
    is_negotiable: bool = True
    dealer_id: Optional[str] = None
    features: List[dict] = []  # [{name, value, category}]
    # Contact preferences
    phone_country_code: Optional[str] = Field(default=None, max_length=8)
    phone_number: Optional[str] = Field(default=None, max_length=40)
    contact_methods: Optional[List[str]] = Field(
        default=None,
        description="Allowed values: PHONE, WHATSAPP, VIBER, TELEGRAM, CHAT",
    )


class CarUpdate(BaseModel):
    model_config = _BASE_CONFIG
    category_id: Optional[str] = None
    location_id: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    price: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=8)
    mileage: Optional[int] = Field(default=None, ge=0)
    vin: Optional[str] = Field(default=None, max_length=40)
    body_type: Optional[str] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    engine: Optional[str] = None
    engine_size: Optional[float] = None
    horsepower: Optional[int] = Field(default=None, ge=0)
    exterior_color: Optional[str] = None
    interior_color: Optional[str] = None
    doors: Optional[int] = Field(default=None, ge=1)
    seats: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    condition: Optional[str] = None
    is_negotiable: Optional[bool] = None
    phone_country_code: Optional[str] = Field(default=None, max_length=8)
    phone_number: Optional[str] = Field(default=None, max_length=40)
    contact_methods: Optional[List[str]] = Field(default=None)


class StatusUpdateRequest(BaseModel):
    status: str


class CarAdminOut(CarDetailOut):
    seller_id: str
    dealer_id: Optional[str] = None
    rejection_reason: Optional[str] = None


class CarStatsOut(ORMBase):
    total: int
    active: int
    pending: int
    sold: int
    draft: int
    rejected: int