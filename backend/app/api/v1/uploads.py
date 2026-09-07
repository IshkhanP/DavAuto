"""File upload API for car images and videos.

The upload is performed by a storage abstraction (local FS in development,
S3-compatible in production).  The database stores only metadata / keys /
URLs — never raw file bytes.
"""
from __future__ import annotations
import io
import os
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.car import Car, CarImage, CarVideo
from app.models.user import User
from app.permissions.rbac import get_current_user
from app.services.storage import get_storage

router = APIRouter(prefix="/uploads", tags=["uploads"])


def _read_validate(file: UploadFile, allowed_types: list[str], max_size_mb: int) -> bytes:
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    data = file.file.read() if hasattr(file.file, "read") else b""
    file.file.seek(0)

    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f}MB > {max_size_mb}MB)")
    return data


def _detect_image_size(data: bytes) -> tuple[Optional[int], Optional[int]]:
    try:
        img = Image.open(io.BytesIO(data))
        return img.size
    except Exception:
        return None, None


@router.post("/cars/{car_id}/images")
async def upload_car_image(
    car_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.execute(
        select(Car)
        .where(Car.id == uuid.UUID(car_id))
        .options(selectinload(Car.images))
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    is_admin = any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles)
    if car.seller_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    data = _read_validate(file, settings.allowed_image_types_list, settings.MAX_UPLOAD_SIZE_MB)
    width, height = _detect_image_size(data)

    storage = get_storage()
    meta = await storage.save(file, key_prefix=f"cars/{car.seller_id}/images")

    image = CarImage(
        car_id=car.id,
        storage_key=meta["key"],
        url=meta["url"],
        original_filename=meta["original_filename"],
        content_type=meta["content_type"],
        size_bytes=meta["size"],
        width=width,
        height=height,
        display_order=len(car.images),
    )
    db.add(image)
    db.flush()

    return {
        "id": str(image.id),
        "key": image.storage_key,
        "url": image.url,
        "width": width,
        "height": height,
        "display_order": image.display_order,
    }


@router.delete("/cars/images/{image_id}")
async def delete_car_image(
    image_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image = db.get(CarImage, uuid.UUID(image_id))
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    car = db.get(Car, image.car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    is_admin = any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles)
    if car.seller_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    storage = get_storage()
    await storage.delete(image.storage_key)
    db.delete(image)
    db.commit()
    return {"deleted": True}


@router.post("/cars/{car_id}/images/{image_id}/main")
async def set_main_image(
    car_id: str,
    image_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.execute(
        select(Car)
        .where(Car.id == uuid.UUID(car_id))
        .options(selectinload(Car.images))
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    is_admin = any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles)
    if car.seller_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    image = db.get(CarImage, uuid.UUID(image_id))
    if not image or image.car_id != car.id:
        raise HTTPException(status_code=404, detail="Image not found on this car")

    for img in car.images:
        img.is_main = (img.id == image.id)
    db.commit()
    return {"ok": True}


@router.put("/cars/{car_id}/images/reorder")
async def reorder_images(
    car_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accepts ``{"image_ids": ["id1", "id2", ...]}`` and sets ``display_order``
    on each CarImage accordingly.  The first id in the list becomes the cover
    (``display_order = 0``).
    """
    car = db.execute(
        select(Car)
        .where(Car.id == uuid.UUID(car_id))
        .options(selectinload(Car.images))
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    is_admin = any(r.role.slug in ("ADMIN", "SUPER_ADMIN") for r in user.roles)
    if car.seller_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    # Defensive: FastAPI hands us an arbitrary dict here because we used
    # ``payload: dict`` for flexibility.  Pydantic v2 will reject unknown
    # top-level keys unless we set ``extra='allow'``.  Rather than rely on
    # extra config, pull out the field we actually need.
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    image_ids = payload.get("image_ids") or []
    if not isinstance(image_ids, list) or not image_ids:
        raise HTTPException(status_code=400, detail="image_ids must be a non-empty list")

    # Coerce any UUIDs to their canonical string form.
    image_ids = [str(i) for i in image_ids]

    images_by_id = {str(img.id): img for img in car.images}
    if set(image_ids) - set(images_by_id.keys()):
        raise HTTPException(
            status_code=400,
            detail="Some image_ids do not belong to this listing",
        )

    for idx, img_id in enumerate(image_ids):
        images_by_id[img_id].display_order = idx
    db.commit()
    return {"ok": True, "count": len(image_ids)}


@router.post("/cars/{car_id}/videos")
async def upload_car_video(
    car_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    car = db.execute(
        select(Car)
        .where(Car.id == uuid.UUID(car_id))
        .options(selectinload(Car.videos))
    ).scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if car.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    _read_validate(file, settings.allowed_video_types_list, settings.MAX_UPLOAD_SIZE_MB * 4)
    storage = get_storage()
    meta = await storage.save(file, key_prefix=f"cars/{car.seller_id}/videos")

    video = CarVideo(
        car_id=car.id,
        storage_key=meta["key"],
        url=meta["url"],
        display_order=len(car.videos),
    )
    db.add(video)
    db.flush()
    return {"id": str(video.id), "url": video.url}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = _read_validate(file, settings.allowed_image_types_list, settings.MAX_UPLOAD_SIZE_MB)
    storage = get_storage()
    meta = await storage.save(file, key_prefix=f"avatars/{user.id}")
    user.avatar_url = meta["url"]
    db.commit()
    return {"url": user.avatar_url}