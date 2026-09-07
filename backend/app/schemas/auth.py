"""Auth-related schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import re

from app.schemas.common import ORMBase


# Permissive email validator: accepts any RFC-5322-ish "local@domain" form,
# including reserved TLDs like ``.local`` and ``.test`` that Pydantic's
# built-in ``EmailStr`` would reject (RFC 6761).  Local development uses
# ``@blacksharkcars.local`` for demo users, so we must be lenient.
_LOCAL_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    if not isinstance(value, str) or not _LOCAL_EMAIL_RE.match(value):
        raise ValueError("Invalid email address")
    return value.lower()


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=40)
    city: Optional[str] = Field(default=None, max_length=120)

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        return _validate_email(v)
    country: Optional[str] = Field(default=None, max_length=80)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]",v) or not re.search(r"\d", v):
            raise ValueError("Password must include letters and numbers")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        return _validate_email(v)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        return _validate_email(v)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


class UserPublic(ORMBase):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    status: str
    is_email_verified: bool
    created_at: datetime


class UserPrivate(UserPublic):
    roles: List[str] = []
    permissions: List[str] = []


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=40)
    city: Optional[str] = Field(default=None, max_length=120)
    country: Optional[str] = Field(default=None, max_length=80)
    bio: Optional[str] = Field(default=None, max_length=500)
    avatar_url: Optional[str] = Field(default=None, max_length=500)