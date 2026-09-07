"""Role/permission/admin schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMBase
# Reuse the permissive email validator from the auth schemas.
from app.schemas.auth import _validate_email


class PermissionOut(ORMBase):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    category: str


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    slug: str = Field(min_length=2, max_length=60)
    description: Optional[str] = None
    permission_ids: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=60)
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class RoleOut(ORMBase):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    is_system: bool
    is_default: bool
    permissions: List[PermissionOut] = []
    created_at: datetime
    updated_at: datetime


class AdminCreateRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    role_id: str
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        return _validate_email(v)


class AdminUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[str] = None
    status: Optional[str] = None


class AdminOut(ORMBase):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    status: str
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    roles: List[str] = []
    created_at: datetime


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None
    is_email_verified: Optional[bool] = None


class AdminUserOut(AdminOut):
    cars_count: int = 0


class AssignRoleRequest(BaseModel):
    role_id: str


class AuditLogOut(ORMBase):
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata_json: Optional[dict] = None
    created_at: datetime


class DashboardStats(ORMBase):
    total_users: int
    active_users: int
    total_listings: int
    active_listings: int
    pending_listings: int
    sold_listings: int
    total_dealers: int
    total_reports: int
    pending_reports: int
    total_messages: int
    total_revenue: float
    new_users_last_30d: int
    new_listings_last_30d: int