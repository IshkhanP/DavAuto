from fastapi import APIRouter

from app.api.v1 import (
    auth, cars, uploads, favorites, messaging, notifications,
    catalog, dealers, reports, admin, super_admin,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(cars.router)
api_router.include_router(uploads.router)
api_router.include_router(favorites.router)
api_router.include_router(messaging.router)
api_router.include_router(notifications.router)
api_router.include_router(catalog.router)
api_router.include_router(dealers.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
api_router.include_router(super_admin.router)