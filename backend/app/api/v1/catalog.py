"""Public catalog endpoints: categories, makes, models, locations.

These are read-only for the public.  Super-admin / content-manager routes
live in the super-admin router.

Each endpoint builds its Pydantic response from a plain ``dict`` (not
``from_attributes`` on the ORM instance) so the ``BeforeValidator`` on
``UUIDStr`` fields fires and converts every ``uuid.UUID`` to a string
before the response is serialized.
"""
from __future__ import annotations
from typing import Any, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.catalog import Category, Make, Model as CarModel, Location
from app.schemas.catalog import CategoryOut, MakeOut, ModelOut, LocationOut
from app.schemas.common import _stringify_uuids

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _model_to_dict(obj: Any) -> dict:
    """Pull attributes off a SQLAlchemy model and stringify any UUIDs.

    We use this instead of ``Model.model_validate(obj)`` (which uses
    ``from_attributes=True`` under the hood) because Pydantic v2 does NOT
    run ``BeforeValidator`` on attribute access.  Going through a dict
    invokes the validators normally.
    """
    data = {
        c.key: getattr(obj, c.key)
        for c in obj.__table__.columns
    }
    return _stringify_uuids(data)


@router.get("/categories", response_model=List[CategoryOut])
def list_categories(active_only: bool = True, db: Session = Depends(get_db)):
    stmt = select(Category).order_by(Category.display_order, Category.name)
    if active_only:
        stmt = stmt.where(Category.is_active == True)  # noqa: E712
    return [CategoryOut.model_validate(_model_to_dict(c)) for c in db.execute(stmt).scalars().all()]


@router.get("/makes", response_model=List[MakeOut])
def list_makes(active_only: bool = True, db: Session = Depends(get_db)):
    stmt = select(Make).order_by(Make.name)
    if active_only:
        stmt = stmt.where(Make.is_active == True)  # noqa: E712
    return [MakeOut.model_validate(_model_to_dict(m)) for m in db.execute(stmt).scalars().all()]


@router.get("/makes/{make_id}/models", response_model=List[ModelOut])
def list_models_for_make(
    make_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    stmt = select(CarModel).where(CarModel.make_id == uuid_module.UUID(make_id)).order_by(CarModel.name)
    if active_only:
        stmt = stmt.where(CarModel.is_active == True)  # noqa: E712
    return [ModelOut.model_validate(_model_to_dict(m)) for m in db.execute(stmt).scalars().all()]


@router.get("/locations", response_model=List[LocationOut])
def list_locations(
    active_only: bool = True,
    country: str = None,
    db: Session = Depends(get_db),
):
    stmt = select(Location).order_by(Location.country, Location.city)
    if active_only:
        stmt = stmt.where(Location.is_active == True)  # noqa: E712
    if country:
        stmt = stmt.where(Location.country == country)
    return [LocationOut.model_validate(_model_to_dict(l)) for l in db.execute(stmt).scalars().all()]


@router.get("/locations/countries", response_model=List[str])
def list_countries(db: Session = Depends(get_db)):
    rows = db.execute(select(Location.country).distinct().order_by(Location.country)).all()
    return [r[0] for r in rows]