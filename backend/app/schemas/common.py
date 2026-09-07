"""Generic / shared Pydantic schemas."""
import uuid
from typing import Annotated, Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, BeforeValidator, ConfigDict, model_serializer, model_validator

T = TypeVar("T")


def _coerce_uuid_to_str(v: Any) -> Any:
    """Convert any UUID-like input to a string.

    Used both as a per-field ``BeforeValidator`` (works for dict inputs) and
    inside the ``model_serializer`` (which always runs, even in
    ``from_attributes`` mode).
    """
    if isinstance(v, uuid.UUID):
        return str(v)
    if hasattr(v, "hex") and not isinstance(v, (str, int, float, bool)):
        return str(v)
    return v


# Type alias to use wherever a field accepts either a UUID or a string.
UUIDStr = Annotated[str, BeforeValidator(_coerce_uuid_to_str)]


def _stringify_uuids(obj: Any) -> Any:
    """Recursively convert any UUID values inside a (possibly nested) structure
    to strings.
    """
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _stringify_uuids(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        coerced = [_stringify_uuids(v) for v in obj]
        return type(obj)(coerced) if isinstance(obj, tuple) else coerced
    return obj


def orm_to_dict(obj: Any) -> dict:
    """Build a ``dict`` from a SQLAlchemy ORM model with all UUID columns
    stringified.  Use this when building a Pydantic response model from
    an ORM row:

        Out.model_validate(orm_to_dict(row))

    This is more reliable than ``Out.model_validate(row)`` because
    Pydantic v2 does not run ``BeforeValidator`` on attribute access in
    ``from_attributes=True`` mode.  Going through a dict (with UUIDs
    already converted) makes the validators fire normally.
    """
    if obj is None:
        return {}
    if hasattr(obj, "__table__"):
        data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    elif hasattr(obj, "__dict__"):
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:
        return obj
    return _stringify_uuids(data)


class ORMBase(BaseModel):
    """Base class for Pydantic models that read from SQLAlchemy ORM rows.

    The ``wrap``-mode ``model_serializer`` runs **after** FastAPI/Pydantic
    builds the output, regardless of whether the input was a dict or an
    ORM instance.  This is the only hook that fires reliably in
    ``from_attributes`` mode and guarantees every ``uuid.UUID`` in the
    payload is rendered as a string in the JSON response.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_serializer(mode="wrap")
    def _ser(self, handler):
        data = handler(self)
        return _stringify_uuids(data)


class Pagination(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    limit: int
    total: int
    total_pages: int

    @classmethod
    def build(cls, items: List[T], page: int, limit: int, total: int) -> "PaginatedResponse[T]":
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        return cls(items=items, page=page, limit=limit, total=total, total_pages=total_pages)


class APIError(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


class MessageResponse(BaseModel):
    message: str


class IDResponse(BaseModel):
    id: UUIDStr