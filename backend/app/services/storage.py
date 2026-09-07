"""Storage abstraction: local filesystem or S3-compatible object storage."""
from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, key_prefix: str) -> dict:
        """Persist a file and return metadata dict with 'key', 'url', 'size', 'content_type'."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file by its storage key."""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Public URL for the file."""


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_path: str, public_url: str):
        self.base_path = base_path
        self.public_url = public_url.rstrip("/")
        os.makedirs(self.base_path, exist_ok=True)

    def _write_file_sync(self, abs_path: str, data: bytes) -> int:
        """Write data to file synchronously. Runs in thread pool."""
        directory = os.path.dirname(abs_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(data)
        return len(data)

    async def save(self, file: UploadFile, key_prefix: str) -> dict:
        ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
        unique_name = f"{uuid4().hex}{ext}"
        rel_path = os.path.join(key_prefix.strip("/"), unique_name).replace("\\", "/")
        abs_path = os.path.join(self.base_path, rel_path)

        # Read file content (FastAPI UploadFile.read is async)
        data = await file.read()
        size = len(data)

        # Write to disk in thread pool to avoid blocking
        await asyncio.to_thread(self._write_file_sync, abs_path, data)
        await file.seek(0)

        return {
            "key": rel_path,
            "url": f"{self.public_url}/{rel_path}",
            "size": size,
            "content_type": file.content_type,
            "original_filename": file.filename,
        }

    async def delete(self, key: str) -> bool:
        path = os.path.join(self.base_path, key)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    def get_url(self, key: str) -> str:
        return f"{self.public_url}/{key}"


class S3StorageBackend(StorageBackend):
    """S3-compatible object storage. Uses boto3 when STORAGE_TYPE=s3."""

    def __init__(self):
        import boto3

        self.bucket = settings.STORAGE_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.STORAGE_REGION,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            endpoint_url=settings.STORAGE_ENDPOINT_URL,
        )

    async def save(self, file: UploadFile, key_prefix: str) -> dict:
        ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
        key = f"{key_prefix.strip('/')}/{uuid4().hex}{ext}"
        body = await file.read()
        size = len(body)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=file.content_type,
        )
        await file.seek(0)
        return {
            "key": key,
            "url": self.get_url(key),
            "size": size,
            "content_type": file.content_type,
            "original_filename": file.filename,
        }

    async def delete(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def get_url(self, key: str) -> str:
        if settings.STORAGE_ENDPOINT_URL:
            return f"{settings.STORAGE_ENDPOINT_URL.rstrip('/')}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{settings.STORAGE_REGION}.amazonaws.com/{key}"


def get_storage() -> StorageBackend:
    """Factory that returns the active storage backend."""
    if settings.STORAGE_TYPE.lower() == "s3":
        return S3StorageBackend()
    return LocalStorageBackend(settings.STORAGE_LOCAL_PATH, settings.STORAGE_PUBLIC_URL)