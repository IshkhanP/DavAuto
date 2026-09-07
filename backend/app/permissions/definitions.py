"""Permission codes used across the application.

Every protected endpoint should reference one of these codes via the
``require_permission`` dependency.  Adding new permissions here is the
single source of truth — they get seeded into the database on startup.
"""
from typing import Dict, List


class PermissionCodes:
    # Users / accounts
    VIEW_USERS = "VIEW_USERS"
    MANAGE_USERS = "MANAGE_USERS"

    # Listings
    VIEW_LISTINGS = "VIEW_LISTINGS"
    MANAGE_LISTINGS = "MANAGE_LISTINGS"
    APPROVE_LISTINGS = "APPROVE_LISTINGS"

    # Reports
    VIEW_REPORTS = "VIEW_REPORTS"
    MANAGE_REPORTS = "MANAGE_REPORTS"

    # Dealers
    MANAGE_DEALERS = "MANAGE_DEALERS"

    # Catalog
    MANAGE_CATEGORIES = "MANAGE_CATEGORIES"
    MANAGE_MAKES = "MANAGE_MAKES"
    MANAGE_MODELS = "MANAGE_MODELS"
    MANAGE_LOCATIONS = "MANAGE_LOCATIONS"

    # Promotions / payments
    MANAGE_PROMOTIONS = "MANAGE_PROMOTIONS"
    VIEW_PAYMENTS = "VIEW_PAYMENTS"
    MANAGE_PAYMENTS = "MANAGE_PAYMENTS"

    # Analytics
    VIEW_ANALYTICS = "VIEW_ANALYTICS"

    # Content
    MANAGE_CONTENT = "MANAGE_CONTENT"

    # Reviews
    MANAGE_REVIEWS = "MANAGE_REVIEWS"

    # Audit
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"

    # System
    MANAGE_SETTINGS = "MANAGE_SETTINGS"
    MANAGE_SECURITY = "MANAGE_SECURITY"


# Bundles of permissions assigned to predefined roles
ROLE_PERMISSION_MATRIX: Dict[str, List[str]] = {
    "SUPER_ADMIN": [v for k, v in vars(PermissionCodes).items() if not k.startswith("_")],

    "ADMIN": [
        PermissionCodes.VIEW_USERS,
        PermissionCodes.MANAGE_USERS,
        PermissionCodes.VIEW_LISTINGS,
        PermissionCodes.MANAGE_LISTINGS,
        PermissionCodes.APPROVE_LISTINGS,
        PermissionCodes.VIEW_REPORTS,
        PermissionCodes.MANAGE_REPORTS,
        PermissionCodes.MANAGE_DEALERS,
        PermissionCodes.VIEW_ANALYTICS,
        PermissionCodes.MANAGE_CATEGORIES,
        PermissionCodes.MANAGE_MAKES,
        PermissionCodes.MANAGE_MODELS,
        PermissionCodes.MANAGE_LOCATIONS,
        PermissionCodes.MANAGE_PROMOTIONS,
        PermissionCodes.MANAGE_REVIEWS,
        PermissionCodes.VIEW_AUDIT_LOGS,
    ],

    "MODERATOR": [
        PermissionCodes.VIEW_LISTINGS,
        PermissionCodes.MANAGE_LISTINGS,
        PermissionCodes.APPROVE_LISTINGS,
        PermissionCodes.VIEW_REPORTS,
        PermissionCodes.MANAGE_REPORTS,
        PermissionCodes.VIEW_USERS,
    ],

    "LISTING_MANAGER": [
        PermissionCodes.VIEW_LISTINGS,
        PermissionCodes.MANAGE_LISTINGS,
        PermissionCodes.APPROVE_LISTINGS,
    ],

    "USER_MANAGER": [
        PermissionCodes.VIEW_USERS,
        PermissionCodes.MANAGE_USERS,
    ],

    "DEALER_MANAGER": [
        PermissionCodes.MANAGE_DEALERS,
        PermissionCodes.VIEW_USERS,
    ],

    "CONTENT_MANAGER": [
        PermissionCodes.MANAGE_CONTENT,
        PermissionCodes.MANAGE_CATEGORIES,
        PermissionCodes.MANAGE_MAKES,
        PermissionCodes.MANAGE_MODELS,
        PermissionCodes.MANAGE_LOCATIONS,
    ],

    "FINANCE_MANAGER": [
        PermissionCodes.VIEW_PAYMENTS,
        PermissionCodes.MANAGE_PAYMENTS,
        PermissionCodes.MANAGE_PROMOTIONS,
        PermissionCodes.VIEW_ANALYTICS,
    ],

    "DEALER": [
        # dealers don't have admin permissions but get a role to manage their store
    ],

    "USER": [],

    "GUEST": [],
}


PERMISSION_METADATA: Dict[str, Dict[str, str]] = {
    PermissionCodes.VIEW_USERS: {"category": "users", "name": "View Users", "description": "View user list and details"},
    PermissionCodes.MANAGE_USERS: {"category": "users", "name": "Manage Users", "description": "Edit, suspend, ban users"},

    PermissionCodes.VIEW_LISTINGS: {"category": "listings", "name": "View Listings", "description": "View all listings"},
    PermissionCodes.MANAGE_LISTINGS: {"category": "listings", "name": "Manage Listings", "description": "Edit or hide any listing"},
    PermissionCodes.APPROVE_LISTINGS: {"category": "listings", "name": "Approve Listings", "description": "Approve or reject pending listings"},

    PermissionCodes.VIEW_REPORTS: {"category": "reports", "name": "View Reports", "description": "View abuse / scam reports"},
    PermissionCodes.MANAGE_REPORTS: {"category": "reports", "name": "Manage Reports", "description": "Resolve or escalate reports"},

    PermissionCodes.MANAGE_DEALERS: {"category": "dealers", "name": "Manage Dealers", "description": "Approve, suspend, verify dealers"},

    PermissionCodes.MANAGE_CATEGORIES: {"category": "catalog", "name": "Manage Categories", "description": "Create and edit categories"},
    PermissionCodes.MANAGE_MAKES: {"category": "catalog", "name": "Manage Makes", "description": "Create and edit makes"},
    PermissionCodes.MANAGE_MODELS: {"category": "catalog", "name": "Manage Models", "description": "Create and edit vehicle models"},
    PermissionCodes.MANAGE_LOCATIONS: {"category": "catalog", "name": "Manage Locations", "description": "Create and edit locations"},

    PermissionCodes.MANAGE_PROMOTIONS: {"category": "promotions", "name": "Manage Promotions", "description": "Configure promotion packages"},
    PermissionCodes.VIEW_PAYMENTS: {"category": "payments", "name": "View Payments", "description": "View payment records"},
    PermissionCodes.MANAGE_PAYMENTS: {"category": "payments", "name": "Manage Payments", "description": "Refund or cancel payments"},

    PermissionCodes.VIEW_ANALYTICS: {"category": "analytics", "name": "View Analytics", "description": "View charts and reports"},

    PermissionCodes.MANAGE_CONTENT: {"category": "content", "name": "Manage Content", "description": "Manage static content"},

    PermissionCodes.MANAGE_REVIEWS: {"category": "reviews", "name": "Manage Reviews", "description": "Approve or remove reviews"},

    PermissionCodes.VIEW_AUDIT_LOGS: {"category": "system", "name": "View Audit Logs", "description": "View system audit logs"},
    PermissionCodes.MANAGE_SETTINGS: {"category": "system", "name": "Manage Settings", "description": "Update site settings"},
    PermissionCodes.MANAGE_SECURITY: {"category": "system", "name": "Manage Security", "description": "Security configuration"},
}