"""Public and authenticated car/listing endpoints."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid as uuid_module

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.car import Car
from app.models.catalog import Make, Model as CarModel, Category, Location
from app.models.user import User
from app.models.enums import CarStatus
from app.permissions.rbac import get_current_user, get_current_user_optional
from app.repositories.car_repository import CarRepository
from app.schemas.car import (
    CarCardOut, CarDetailOut, CarCreate, CarUpdate,
    CarAdminOut, SellerSummary, StatusUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.audit import log_action

router = APIRouter(prefix="/cars", tags=["cars"])


def repo_get_with_details(db: Session, car_id):
    repo = CarRepository(db)
    return repo.get_with_details(car_id)


def _to_card(car: Car, repo: CarRepository) -> CarCardOut:
    main_image = repo.get_main_image_url(car)
    return CarCardOut.model_validate({
        "id": str(car.id),
        "make": car.make.name if car.make else "",
        "model": car.model.name if car.model else "",
        "year": car.year,
        "price": float(car.price),
        "currency": car.currency,
        "mileage": car.mileage,
        "fuel_type": car.fuel_type,
        "transmission": car.transmission,
        "body_type": car.body_type,
        "city": car.location.city if car.location else None,
        "country": car.location.country if car.location else None,
        "status": car.status,
        "is_featured": car.is_featured,
        "is_promoted": car.is_promoted,
        "views_count": car.views_count,
        "favorites_count": car.favorites_count,
        "main_image": main_image,
        "published_at": car.published_at,
        "seller_type": "DEALER" if car.dealer_id else "USER",
    })


def _to_detail(car: Car) -> CarDetailOut:
    location_display = None
    if car.location:
        location_display = ", ".join(filter(None, [car.location.city, car.location.country]))

    seller = car.seller

    images = sorted(car.images, key=lambda i: (not i.is_main, i.display_order))
    return CarDetailOut.model_validate({
        "id": str(car.id),
        "make_id": str(car.make_id),
        "model_id": str(car.model_id),
        "make_name": car.make.name if car.make else "",
        "model_name": car.model.name if car.model else "",
        "category_id": str(car.category_id) if car.category_id else None,
        "category_name": car.category.name if car.category else None,
        "year": car.year,
        "price": float(car.price),
        "currency": car.currency,
        "mileage": car.mileage,
        "vin": car.vin,
        "body_type": car.body_type,
        "fuel_type": car.fuel_type,
        "transmission": car.transmission,
        "drive_type": car.drive_type,
        "engine": car.engine,
        "engine_size": float(car.engine_size) if car.engine_size is not None else None,
        "horsepower": car.horsepower,
        "exterior_color": car.exterior_color,
        "interior_color": car.interior_color,
        "doors": car.doors,
        "seats": car.seats,
        "description": car.description,
        "condition": car.condition,
        "status": car.status,
        "is_featured": car.is_featured,
        "is_promoted": car.is_promoted,
        "is_negotiable": car.is_negotiable,
        "views_count": car.views_count,
        "favorites_count": car.favorites_count,
        "published_at": car.published_at,
        "expires_at": car.expires_at,
        "sold_at": car.sold_at,
        "created_at": car.created_at,
        "updated_at": car.updated_at,
        "images": [
            {
                "id": str(i.id),
                "url": i.url,
                "thumbnail_url": i.thumbnail_url,
                "display_order": i.display_order,
                "is_main": i.is_main,
                "width": i.width,
                "height": i.height,
            }
            for i in images
        ],
        "videos": [
            {
                "id": str(v.id),
                "url": v.url,
                "thumbnail_url": v.thumbnail_url,
                "duration_seconds": v.duration_seconds,
            }
            for v in car.videos
        ],
        "features": [
            {
                "id": str(f.id),
                "name": f.name,
                "value": f.value,
                "category": f.category,
            }
            for f in car.features
        ],
        "seller": {
            "id": str(seller.id),
            "full_name": seller.full_name,
            "avatar_url": seller.avatar_url,
            "city": seller.city,
            "country": seller.country,
            "seller_type": "DEALER" if car.dealer_id else "USER",
        },
        "location_display": location_display,
        "phone_country_code": car.phone_country_code,
        "phone_number": car.phone_number,
        "contact_methods": [
            m.strip() for m in (car.contact_methods or "").split(",") if m.strip()
        ],
    })


@router.get("", response_model=PaginatedResponse[CarCardOut])
def list_cars(
    request: Request,
    make: Optional[str] = None,
    make_id: Optional[str] = None,
    model: Optional[str] = None,
    model_id: Optional[str] = None,
    category_id: Optional[str] = None,
    body_type: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    drive_type: Optional[str] = None,
    condition: Optional[str] = None,
    location_id: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    seller_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_mileage: Optional[int] = None,
    max_mileage: Optional[int] = None,
    color: Optional[str] = None,
    q: Optional[str] = None,
    is_featured: Optional[bool] = None,
    sort: str = "newest",
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    items, total = repo.list_paginated(
        page=page, limit=limit,
        status=CarStatus.ACTIVE.value,
        make=make, make_id=make_id, model=model, model_id=model_id,
        category_id=category_id, body_type=body_type, fuel_type=fuel_type,
        transmission=transmission, drive_type=drive_type, condition=condition,
        location_id=location_id, city=city, country=country,
        seller_type=seller_type,
        min_price=min_price, max_price=max_price,
        min_year=min_year, max_year=max_year,
        min_mileage=min_mileage, max_mileage=max_mileage,
        color=color, q=q, is_featured=is_featured, sort=sort,
    )
    cards = [_to_card(car, repo) for car in items]
    return PaginatedResponse[CarCardOut].build(cards, page, limit, total)


@router.get("/featured", response_model=List[CarCardOut])
def featured_cars(
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    items, _ = repo.list_paginated(
        page=1, limit=limit, status=CarStatus.ACTIVE.value,
        is_featured=True, sort="newest",
    )
    return [_to_card(c, repo) for c in items]


@router.get("/latest", response_model=List[CarCardOut])
def latest_cars(
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    items, _ = repo.list_paginated(
        page=1, limit=limit, status=CarStatus.ACTIVE.value, sort="newest",
    )
    return [_to_card(c, repo) for c in items]


@router.get("/similar/{car_id}", response_model=List[CarCardOut])
def similar_cars(car_id: str, limit: int = Query(8, ge=1, le=50), db: Session = Depends(get_db)):
    repo = CarRepository(db)
    car = repo.get_with_details(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    items, _ = repo.list_paginated(
        page=1, limit=limit, status=CarStatus.ACTIVE.value,
        make_id=str(car.make_id), model_id=str(car.model_id),
    )
    cards = [_to_card(c, repo) for c in items if str(c.id) != str(car.id)]
    if len(cards) < limit:
        # backfill by make
        more, _ = repo.list_paginated(
            page=1, limit=limit * 2, status=CarStatus.ACTIVE.value, make_id=str(car.make_id),
        )
        for c in more:
            if len(cards) >= limit:
                break
            if str(c.id) == str(car.id) or any(str(x.id) == str(c.id) for x in cards):
                continue
            cards.append(_to_card(c, repo))
    return cards[:limit]


@router.get("/{car_id}", response_model=CarDetailOut)
def get_car(
    car_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    repo = CarRepository(db)
    car = repo.get_with_details(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if car.status not in (CarStatus.ACTIVE.value, CarStatus.SOLD.value):
        if not current_user or (
            current_user.id != car.seller_id and not any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in current_user.roles)
        ):
            raise HTTPException(status_code=404, detail="Car not found")

    # increment views asynchronously-safe (here synchronous)
    if not current_user or current_user.id != car.seller_id:
        repo.increment_views(car.id)
        db.commit()

    return _to_detail(car)


# ----- Authenticated endpoints (CRUD for owner) -----
@router.post("", response_model=CarDetailOut, status_code=201)
async def create_car(
    payload: CarCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate FKs
    make = db.get(Make, uuid_module.UUID(payload.make_id)) if payload.make_id else None
    if not make:
        raise HTTPException(status_code=400, detail="Invalid make")
    model = db.get(CarModel, uuid_module.UUID(payload.model_id)) if payload.model_id else None
    if not model or str(model.make_id) != str(make.id):
        raise HTTPException(status_code=400, detail="Invalid model")
    category = None
    if payload.category_id:
        category = db.get(Category, uuid_module.UUID(payload.category_id))
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category")
    location = None
    if payload.location_id:
        location = db.get(Location, uuid_module.UUID(payload.location_id))
        if not location:
            raise HTTPException(status_code=400, detail="Invalid location")

    dealer_id = None
    if payload.dealer_id:
        dealer_id = uuid_module.UUID(payload.dealer_id)

    car = Car(
        seller_id=user.id,
        dealer_id=dealer_id,
        make_id=make.id,
        model_id=model.id,
        category_id=category.id if category else None,
        location_id=location.id if location else None,
        year=payload.year,
        price=payload.price,
        currency=payload.currency or "USD",
        mileage=payload.mileage,
        vin=payload.vin,
        body_type=payload.body_type,
        fuel_type=payload.fuel_type,
        transmission=payload.transmission,
        drive_type=payload.drive_type,
        engine=payload.engine,
        engine_size=payload.engine_size,
        horsepower=payload.horsepower,
        exterior_color=payload.exterior_color,
        interior_color=payload.interior_color,
        doors=payload.doors,
        seats=payload.seats,
        description=payload.description,
        condition=payload.condition or "USED",
        is_negotiable=payload.is_negotiable,
        status=(CarStatus.ACTIVE.value if settings.LISTING_AUTO_APPROVE else CarStatus.PENDING.value),
        published_at=(datetime.now(timezone.utc) if settings.LISTING_AUTO_APPROVE else None),
        expires_at=(datetime.now(timezone.utc) + timedelta(days=settings.LISTING_EXPIRY_DAYS) if settings.LISTING_AUTO_APPROVE else None),
        phone_country_code=payload.phone_country_code,
        phone_number=payload.phone_number,
        contact_methods=(",".join(payload.contact_methods) if payload.contact_methods else "PHONE,CHAT"),
    )
    db.add(car)
    db.flush()

    for f in payload.features or []:
        db.add(CarFeature(car_id=car.id, name=str(f.get("name", ""))[:80], value=f.get("value"), category=f.get("category")))

    log_action(db, action="USER_CREATED_LISTING", user_id=user.id, request=request,
               resource_type="car", resource_id=str(car.id))
    db.commit()
    db.refresh(car)

    return _to_detail(repo_get_with_details(db, car.id))


@router.patch("/{car_id}", response_model=CarDetailOut)
def update_car(
    car_id: str,
    payload: CarUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if car.seller_id != user.id and not any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles):
        raise HTTPException(status_code=403, detail="Not allowed")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if field in ("category_id", "location_id") and value:
            value = uuid_module.UUID(value)
        setattr(car, field, value)

    db.commit()
    return _to_detail(repo_get_with_details(db, car.id))


@router.post("/{car_id}/status", response_model=CarDetailOut)
def change_status(
    car_id: str,
    payload: StatusUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if car.seller_id != user.id and not any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles):
        raise HTTPException(status_code=403, detail="Not allowed")

    new_status = payload.status.upper()
    allowed = {"DRAFT", "PENDING", "ACTIVE", "PAUSED", "SOLD", "DELETED"}
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(allowed)}")

    if new_status == "ACTIVE" and car.status in ("DRAFT", "PAUSED", "PENDING"):
        if not car.published_at:
            car.published_at = datetime.now(timezone.utc)
        if not car.expires_at:
            car.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.LISTING_EXPIRY_DAYS)
    if new_status == "SOLD":
        car.sold_at = datetime.now(timezone.utc)
    if new_status == "DELETED":
        car.status = CarStatus.DELETED.value
        db.commit()
        return {"id": str(car.id)}

    car.status = new_status
    db.commit()
    return _to_detail(repo_get_with_details(db, car.id))


@router.post("/{car_id}/duplicate", response_model=CarDetailOut, status_code=201)
def duplicate_car(
    car_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    src = repo.get_with_details(car_id)
    if not src:
        raise HTTPException(status_code=404, detail="Car not found")
    if src.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_car = Car(
        seller_id=src.seller_id,
        dealer_id=src.dealer_id,
        make_id=src.make_id,
        model_id=src.model_id,
        category_id=src.category_id,
        location_id=src.location_id,
        year=src.year, price=src.price, currency=src.currency,
        mileage=src.mileage, vin=None,
        body_type=src.body_type, fuel_type=src.fuel_type, transmission=src.transmission, drive_type=src.drive_type,
        engine=src.engine, engine_size=src.engine_size, horsepower=src.horsepower,
        exterior_color=src.exterior_color, interior_color=src.interior_color,
        doors=src.doors, seats=src.seats,
        description=src.description, condition=src.condition, is_negotiable=src.is_negotiable,
        status=CarStatus.DRAFT.value,
    )
    db.add(new_car)
    db.flush()

    for img in src.images:
        db.add(CarImage(
            car_id=new_car.id,
            storage_key=img.storage_key,
            url=img.url,
            thumbnail_url=img.thumbnail_url,
            display_order=img.display_order,
            is_main=False,
        ))
    for f in src.features:
        db.add(CarFeature(car_id=new_car.id, name=f.name, value=f.value, category=f.category))

    db.commit()
    return _to_detail(repo.get_with_details(new_car.id))


@router.delete("/{car_id}", status_code=204)
def delete_car(
    car_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    is_admin = any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles)
    if car.seller_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    if car.seller_id == user.id:
        car.status = CarStatus.DELETED.value
    else:
        db.delete(car)

    log_action(db, action="USER_DELETED_LISTING" if not is_admin else "ADMIN_DELETED_LISTING",
               user_id=user.id, request=request, resource_type="car", resource_id=car_id)
    db.commit()
    return None


# ----- My listings -----
@router.get("/mine/all", response_model=PaginatedResponse[CarCardOut])
def my_listings(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    items, total = repo.list_paginated(
        page=page, limit=limit,
        status=status_filter if status_filter else "ACTIVE,DRAFT,PENDING,SOLD,PAUSED,EXPIRED,REJECTED",
        seller_id=str(user.id),
    )
    return PaginatedResponse[CarCardOut].build([_to_card(c, repo) for c in items], page, limit, total)