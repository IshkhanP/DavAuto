"""Repository layer for cars / listings with filter + pagination."""
from __future__ import annotations
from typing import Optional, Tuple, List, Dict, Any
import uuid

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, selectinload, joinedload

from app.models.car import Car, CarImage


SORT_MAP = {
    "newest": ("published_at", "desc"),
    "oldest": ("published_at", "asc"),
    "price_asc": ("price", "asc"),
    "price_desc": ("price", "desc"),
    "mileage_asc": ("mileage", "asc"),
    "mileage_desc": ("mileage", "desc"),
    "year_desc": ("year", "desc"),
    "year_asc": ("year", "asc"),
    "views_desc": ("views_count", "desc"),
}


class CarRepository:
    def __init__(self, db: Session):
        self.db = db

    def build_query(
        self,
        *,
        status: Optional[str] = "ACTIVE",
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
        seller_id: Optional[str] = None,
        seller_type: Optional[str] = None,
        dealer_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_mileage: Optional[int] = None,
        max_mileage: Optional[int] = None,
        color: Optional[str] = None,
        q: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_promoted: Optional[bool] = None,
        sort: str = "newest",
    ):
        stmt = select(Car).options(
            selectinload(Car.images),
            selectinload(Car.make),
            selectinload(Car.model),
            selectinload(Car.category),
            selectinload(Car.location),
            selectinload(Car.dealer),
        )
        conditions = []

        if status is not None:
            if isinstance(status, str) and "," in status:
                conditions.append(Car.status.in_([s.strip() for s in status.split(",")]))
            else:
                conditions.append(Car.status == status)
        if make_id:
            conditions.append(Car.make_id == uuid.UUID(make_id))
        if make:
            conditions.append(Car.make.has(slug=make) | Car.make.has(name=make))
        if model_id:
            conditions.append(Car.model_id == uuid.UUID(model_id))
        if model:
            conditions.append(Car.model.has(slug=model) | Car.model.has(name=model))
        if category_id:
            conditions.append(Car.category_id == uuid.UUID(category_id))
        if body_type:
            conditions.append(Car.body_type == body_type)
        if fuel_type:
            conditions.append(Car.fuel_type == fuel_type)
        if transmission:
            conditions.append(Car.transmission == transmission)
        if drive_type:
            conditions.append(Car.drive_type == drive_type)
        if condition:
            conditions.append(Car.condition == condition)
        if location_id:
            conditions.append(Car.location_id == uuid.UUID(location_id))
        if city:
            conditions.append(Car.location.has(city=city))
        if country:
            conditions.append(Car.location.has(country=country))
        if seller_id:
            conditions.append(Car.seller_id == uuid.UUID(seller_id))
        if dealer_id:
            conditions.append(Car.dealer_id == uuid.UUID(dealer_id))
        if seller_type == "DEALER":
            conditions.append(Car.dealer_id.isnot(None))
        elif seller_type == "USER":
            conditions.append(Car.dealer_id.is_(None))
        if min_price is not None:
            conditions.append(Car.price >= min_price)
        if max_price is not None:
            conditions.append(Car.price <= max_price)
        if min_year is not None:
            conditions.append(Car.year >= min_year)
        if max_year is not None:
            conditions.append(Car.year <= max_year)
        if min_mileage is not None:
            conditions.append(Car.mileage >= min_mileage)
        if max_mileage is not None:
            conditions.append(Car.mileage <= max_mileage)
        if color:
            conditions.append(or_(Car.exterior_color == color, Car.interior_color == color))
        if is_featured is not None:
            conditions.append(Car.is_featured.is_(is_featured))
        if is_promoted is not None:
            conditions.append(Car.is_promoted.is_(is_promoted))
        if q:
            pattern = f"%{q}%"
            conditions.append(
                or_(
                    Car.description.ilike(pattern),
                    Car.make.has(name=pattern),
                    Car.model.has(name=pattern),
                    Car.vin.ilike(pattern),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        col, direction = SORT_MAP.get(sort, SORT_MAP["newest"])
        col_attr = getattr(Car, col)
        if direction == "desc":
            stmt = stmt.order_by(desc(col_attr))
        else:
            stmt = stmt.order_by(asc(col_attr))

        return stmt

    def list_paginated(
        self,
        page: int = 1,
        limit: int = 24,
        **filters: Any,
    ) -> Tuple[List[Car], int]:
        stmt = self.build_query(**filters)
        # total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar() or 0

        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)
        items = list(self.db.execute(stmt).scalars().unique().all())
        return items, total

    def get_with_details(self, car_id: str | uuid.UUID) -> Optional[Car]:
        stmt = (
            select(Car)
            .where(Car.id == (car_id if isinstance(car_id, uuid.UUID) else uuid.UUID(str(car_id))))
            .options(
                selectinload(Car.images),
                selectinload(Car.videos),
                selectinload(Car.features),
                selectinload(Car.make),
                selectinload(Car.model),
                selectinload(Car.category),
                selectinload(Car.location),
                selectinload(Car.dealer),
                selectinload(Car.seller),
            )
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def increment_views(self, car_id: uuid.UUID) -> None:
        self.db.execute(
            Car.__table__.update().where(Car.id == car_id).values(views_count=Car.views_count + 1)
        )

    def get_main_image_url(self, car: Car) -> Optional[str]:
        if not car.images:
            return None
        main = next((i for i in car.images if i.is_main), None)
        return (main or car.images[0]).url

    def stats(self) -> Dict[str, int]:
        rows = self.db.execute(
            select(Car.status, func.count(Car.id)).group_by(Car.status)
        ).all()
        out = {"total": 0, "active": 0, "pending": 0, "sold": 0, "draft": 0, "rejected": 0}
        for status, count in rows:
            out["total"] += count
            out[status.lower()] = count
        return out