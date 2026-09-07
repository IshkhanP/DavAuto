"""Dealer endpoints (public + authenticated dealer owner)."""
from __future__ import annotations
from typing import Optional, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole, Role
from app.models.dealer import Dealer, DealerEmployee
from app.models.car import Car
from app.models.enums import CarStatus
from app.permissions.rbac import get_current_user
from app.repositories.car_repository import CarRepository
from app.schemas.common import PaginatedResponse, _stringify_uuids
from app.schemas.car import CarCardOut
from app.schemas.messaging import DealerCreate, DealerUpdate, DealerOut, DealerEmployeeAdd
from app.utils.slug import slugify

router = APIRouter(prefix="/dealers", tags=["dealers"])


def _model_to_dict(obj) -> dict:
    """Pull attributes off a SQLAlchemy model and stringify any UUIDs so
    Pydantic v2 ``BeforeValidator`` fields see plain strings.
    """
    data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
    return _stringify_uuids(data)


@router.get("", response_model=List[DealerOut])
def list_dealers(
    is_verified: Optional[bool] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Dealer).where(Dealer.is_active == True)  # noqa: E712
    if is_verified is not None:
        stmt = stmt.where(Dealer.is_verified == is_verified)
    if country:
        stmt = stmt.where(Dealer.country == country)
    if city:
        stmt = stmt.where(Dealer.city == city)
    stmt = stmt.order_by(Dealer.is_verified.desc(), Dealer.business_name).limit(limit)
    return [DealerOut.model_validate(_model_to_dict(d)) for d in db.execute(stmt).scalars().all()]


@router.get("/{dealer_id}", response_model=DealerOut)
def get_dealer(dealer_id: str, db: Session = Depends(get_db)):
    dealer = db.get(Dealer, uuid_module.UUID(dealer_id))
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    return DealerOut.model_validate(_model_to_dict(dealer))


@router.get("/{dealer_id}/cars", response_model=PaginatedResponse[CarCardOut])
def dealer_cars(
    dealer_id: str,
    page: int = 1,
    limit: int = 24,
    db: Session = Depends(get_db),
):
    dealer = db.get(Dealer, uuid_module.UUID(dealer_id))
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    repo = CarRepository(db)
    items, total = repo.list_paginated(
        page=page, limit=limit,
        status=CarStatus.ACTIVE.value,
        dealer_id=str(dealer.id),
    )
    cards = []
    for car in items:
        cards.append(CarCardOut(
            id=str(car.id),
            make=car.make.name if car.make else "",
            model=car.model.name if car.model else "",
            year=car.year,
            price=float(car.price),
            currency=car.currency,
            mileage=car.mileage,
            fuel_type=car.fuel_type,
            transmission=car.transmission,
            body_type=car.body_type,
            city=car.location.city if car.location else None,
            country=car.location.country if car.location else None,
            status=car.status,
            is_featured=car.is_featured,
            is_promoted=car.is_promoted,
            views_count=car.views_count,
            favorites_count=car.favorites_count,
            main_image=repo.get_main_image_url(car),
            published_at=car.published_at,
            seller_type="DEALER",
        ))
    return PaginatedResponse[CarCardOut].build(cards, page, limit, total)


# ---- Authenticated dealer endpoints ----
@router.post("", response_model=DealerOut, status_code=201)
def create_dealer(
    payload: DealerCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slug = payload.slug or slugify(payload.business_name)
    existing = db.execute(select(Dealer).where(Dealer.slug == slug)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Dealer with this slug already exists")

    dealer = Dealer(
        owner_id=user.id,
        business_name=payload.business_name,
        slug=slug,
        description=payload.description,
        logo_url=payload.logo_url,
        cover_url=payload.cover_url,
        phone=payload.phone,
        email=payload.email,
        website=payload.website,
        address=payload.address,
        city=payload.city,
        country=payload.country,
        working_hours=payload.working_hours,
        social_links=payload.social_links,
    )
    db.add(dealer)

    # Add DEALER role to user if not already
    dealer_role = db.execute(select(Role).where(Role.slug == "DEALER")).scalar_one_or_none()
    if dealer_role and not any(r.role.slug == "DEALER" for r in user.roles):
        user.roles.append(UserRole(role=dealer_role))

    db.commit()
    db.refresh(dealer)
    return dealer


@router.patch("/{dealer_id}", response_model=DealerOut)
def update_dealer(
    dealer_id: str,
    payload: DealerUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dealer = db.get(Dealer, uuid_module.UUID(dealer_id))
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    if dealer.owner_id != user.id and not any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles):
        raise HTTPException(status_code=403, detail="Not allowed")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(dealer, k, v)
    db.commit()
    db.refresh(dealer)
    return dealer


@router.post("/{dealer_id}/employees")
def add_employee(
    dealer_id: str,
    payload: DealerEmployeeAdd,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    dealer = db.get(Dealer, uuid_module.UUID(dealer_id))
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    if dealer.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only owner can add employees")
    existing = db.execute(
        select(DealerEmployee).where(
            DealerEmployee.dealer_id == dealer.id,
            DealerEmployee.user_id == uuid_module.UUID(payload.user_id),
        )
    ).scalar_one_or_none()
    if existing:
        return {"added": False}
    emp = DealerEmployee(dealer_id=dealer.id, user_id=uuid_module.UUID(payload.user_id), position=payload.position)
    db.add(emp)
    db.commit()
    return {"added": True, "id": str(emp.id)}