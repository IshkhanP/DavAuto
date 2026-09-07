"""Application configuration via environment variables."""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "BlackSharkCars"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/blacksharkcars"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_REFRESH_SECRET_KEY: str = "change-me-in-production-too"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Storage
    STORAGE_TYPE: str = "local"  # local | s3
    STORAGE_LOCAL_PATH: str = "./storage/uploads"
    STORAGE_PUBLIC_URL: str = "http://localhost:8000/static"
    STORAGE_BUCKET: Optional[str] = None
    STORAGE_REGION: Optional[str] = None
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_ENDPOINT_URL: Optional[str] = None

    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@blacksharkcars.local"
    SMTP_FROM_NAME: str = "BlackSharkCars"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    # Listing
    LISTING_AUTO_APPROVE: bool = True
    LISTING_EXPIRY_DAYS: int = 60

    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"
    ALLOWED_VIDEO_TYPES: str = "video/mp4,video/webm"

    # Super Admin (seed only)
    SUPER_ADMIN_EMAIL: str = "admin@blacksharkcars.local"
    SUPER_ADMIN_PASSWORD: str = "ChangeMe!2025"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    @property
    def allowed_video_types_list(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_VIDEO_TYPES.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()