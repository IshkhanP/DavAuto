"""Re-exports so Alembic / Base.metadata picks everything up."""
from app.core.database import Base  # noqa: F401

from app.models.user import User, Role, Permission, UserRole, RolePermission, RefreshToken, PasswordResetToken, EmailVerificationToken  # noqa: F401
from app.models.catalog import Category, Make, Model, Location  # noqa: F401
from app.models.car import Car, CarImage, CarVideo, CarFeature, Favorite  # noqa: F401
from app.models.messaging import Conversation, ConversationParticipant, Message, Notification  # noqa: F401
from app.models.dealer import (  # noqa: F401
    Dealer, DealerEmployee, Report, PromotionPackage, UserPromotion,
    Payment, Review, AuditLog, SiteSetting
)
# Import enums under distinct names so they don't shadow the SQLAlchemy models
# (e.g. UserRole model vs UserRole enum).
from app.models import enums as _enums  # noqa: F401

__all__ = [
    "Base",
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "RefreshToken", "PasswordResetToken", "EmailVerificationToken",
    "Category", "Make", "Model", "Location",
    "Car", "CarImage", "CarVideo", "CarFeature", "Favorite",
    "Conversation", "ConversationParticipant", "Message", "Notification",
    "Dealer", "DealerEmployee", "Report", "PromotionPackage", "UserPromotion",
    "Payment", "Review", "AuditLog", "SiteSetting",
]