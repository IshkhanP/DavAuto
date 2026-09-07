"""Favorites endpoints."""
from __future__ import annotations
import uuid as uuid_module
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.car import Car, Favorite
from app.models.user import User
from app.permissions.rbac import get_current_user
from app.repositories.car_repository import CarRepository
from app.schemas.car import CarCardOut
from app.schemas.common import PaginatedResponse
from app.schemas.messaging import FavoriteToggleResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/{car_id}", response_model=FavoriteToggleResponse)
def add_favorite(car_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    existing = db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.car_id == car.id)
    ).scalar_one_or_none()
    if existing:
        return FavoriteToggleResponse(favorited=True, favorites_count=car.favorites_count)

    fav = Favorite(user_id=user.id, car_id=car.id)
    db.add(fav)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return FavoriteToggleResponse(favorited=True, favorites_count=car.favorites_count)

    car.favorites_count = (car.favorites_count or 0) + 1
    db.commit()
    return FavoriteToggleResponse(favorited=True, favorites_count=car.favorites_count)


@router.delete("/{car_id}", response_model=FavoriteToggleResponse)
def remove_favorite(car_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    car = db.get(Car, uuid_module.UUID(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    fav = db.execute(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.car_id == car.id)
    ).scalar_one_or_none()
    if fav:
        db.delete(fav)
        car.favorites_count = max(0, (car.favorites_count or 1) - 1)
        db.commit()
    return FavoriteToggleResponse(favorited=False, favorites_count=car.favorites_count or 0)


@router.get("", response_model=PaginatedResponse[CarCardOut])
def list_favorites(
    page: int = 1,
    limit: int = 24,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = CarRepository(db)
    stmt = (
        select(Car)
        .join(Favorite, Favorite.car_id == Car.id)
        .where(Favorite.user_id == user.id)
        .options(
            selectinload(Car.images),
            selectinload(Car.make),
            selectinload(Car.model),
            selectinload(Car.category),
            selectinload(Car.location),
            selectinload(Car.dealer),
        )
    )
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0
    items = list(db.execute(stmt.offset((page - 1) * limit).limit(limit)).scalars().unique().all())

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
            seller_type="DEALER" if car.dealer_id else "USER",
        ))
    return PaginatedResponse[CarCardOut].build(cards, page, limit, total)