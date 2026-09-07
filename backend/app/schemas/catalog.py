"""Catalog schemas: categories, makes, models, locations."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    slug: str = Field(min_length=2, max_length=80)
    icon: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    icon: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryOut(ORMBase):
    id: str
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MakeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=80)
    logo_url: Optional[str] = None
    is_active: bool = True


class MakeUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


class MakeOut(ORMBase):
    id: str
    name: str
    slug: str
    logo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ModelCreate(BaseModel):
    make_id: str
    name: str = Field(min_length=1, max_length=80)
    slug: str = Field(min_length=1, max_length=80)
    body_type: Optional[str] = None
    is_active: bool = True


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    body_type: Optional[str] = None
    is_active: Optional[bool] = None


class ModelOut(ORMBase):
    id: str
    make_id: str
    name: str
    slug: str
    body_type: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationCreate(BaseModel):
    country: str = Field(min_length=2, max_length=80)
    region: Optional[str] = Field(default=None, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    district: Optional[str] = Field(default=None, max_length=120)
    display_name: str = Field(min_length=2, max_length=255)
    is_active: bool = True


class LocationUpdate(BaseModel):
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None


class LocationOut(ORMBase):
    id: str
    country: str
    region: Optional[str] = None
    city: str
    district: Optional[str] = None
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime