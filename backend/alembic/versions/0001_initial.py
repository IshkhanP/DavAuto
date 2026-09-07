"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ---- users / roles / permissions ----
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(40)),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("bio", sa.String(500)),
        sa.Column("city", sa.String(120)),
        sa.Column("country", sa.String(80)),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_phone_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_2fa_enabled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_ip", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("category", sa.String(60), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(60), nullable=False, unique=True),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.String(255)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ---- catalog ----
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("icon", sa.String(80)),
        sa.Column("description", sa.String(255)),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("country", sa.String(80), nullable=False),
        sa.Column("region", sa.String(120)),
        sa.Column("city", sa.String(120), nullable=False),
        sa.Column("district", sa.String(120)),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_locations_country_city", "locations", ["country", "city"])

    op.create_table(
        "makes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("make_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("makes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("body_type", sa.String(40)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("make_id", "slug", name="uq_make_model_slug"),
    )
    op.create_index("ix_models_make_id", "models", ["make_id"])

    # ---- dealers ----
    op.create_table(
        "dealers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("cover_url", sa.String(500)),
        sa.Column("phone", sa.String(40)),
        sa.Column("email", sa.String(255)),
        sa.Column("website", sa.String(500)),
        sa.Column("address", sa.String(255)),
        sa.Column("city", sa.String(120)),
        sa.Column("country", sa.String(80)),
        sa.Column("working_hours", sa.String(255)),
        sa.Column("social_links", postgresql.JSONB),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_dealers_city", "dealers", ["city"])

    op.create_table(
        "dealer_employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dealer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dealers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.String(80)),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("dealer_id", "user_id", name="uq_dealer_user"),
    )

    # ---- cars ----
    op.create_table(
        "cars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dealer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dealers.id", ondelete="SET NULL")),
        sa.Column("make_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("makes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("model_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("models.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL")),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("mileage", sa.Integer, nullable=False, server_default="0"),
        sa.Column("vin", sa.String(40)),
        sa.Column("body_type", sa.String(40)),
        sa.Column("fuel_type", sa.String(40)),
        sa.Column("transmission", sa.String(40)),
        sa.Column("drive_type", sa.String(40)),
        sa.Column("engine", sa.String(120)),
        sa.Column("engine_size", sa.Numeric(4, 1)),
        sa.Column("horsepower", sa.Integer),
        sa.Column("exterior_color", sa.String(60)),
        sa.Column("interior_color", sa.String(60)),
        sa.Column("doors", sa.Integer),
        sa.Column("seats", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("condition", sa.String(20), nullable=False, server_default="USED"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("rejection_reason", sa.String(500)),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_promoted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_negotiable", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("views_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("favorites_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("sold_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_cars_price", "cars", ["price"])
    op.create_index("ix_cars_year", "cars", ["year"])
    op.create_index("ix_cars_mileage", "cars", ["mileage"])
    op.create_index("ix_cars_status", "cars", ["status"])
    op.create_index("ix_cars_make_id", "cars", ["make_id"])
    op.create_index("ix_cars_model_id", "cars", ["model_id"])
    op.create_index("ix_cars_location_id", "cars", ["location_id"])
    op.create_index("ix_cars_seller_id", "cars", ["seller_id"])
    op.create_index("ix_cars_published_at", "cars", ["published_at"])
    op.create_index("ix_cars_fuel_transmission", "cars", ["fuel_type", "transmission"])
    op.create_index("ix_cars_featured_promoted", "cars", ["is_featured", "is_promoted"])

    op.create_table(
        "car_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("url", sa.String(800), nullable=False),
        sa.Column("thumbnail_url", sa.String(800)),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("content_type", sa.String(60)),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_main", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "car_videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("url", sa.String(800), nullable=False),
        sa.Column("thumbnail_url", sa.String(800)),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "car_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("value", sa.String(120)),
        sa.Column("category", sa.String(60)),
    )

    op.create_table(
        "favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "car_id", name="uq_user_car_favorite"),
    )

    # ---- messaging ----
    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE")),
        sa.Column("subject", sa.String(200)),
        sa.Column("last_message_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "conversation_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_read_at", sa.DateTime(timezone=True)),
        sa.Column("unread_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_blocked", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("data", postgresql.JSONB),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
    )

    # ---- reports ----
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE")),
        sa.Column("reported_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ---- promotions ----
    op.create_table(
        "promotion_packages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("promotion_type", sa.String(40), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("max_active_per_user", sa.Integer, nullable=False, server_default="10"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "user_promotions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promotion_packages.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("promotion_type", sa.String(40), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("promotion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_promotions.id", ondelete="SET NULL")),
        sa.Column("package_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promotion_packages.id", ondelete="SET NULL")),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("provider", sa.String(40)),
        sa.Column("provider_payment_id", sa.String(200)),
        sa.Column("description", sa.String(255)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dealer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dealers.id", ondelete="CASCADE")),
        sa.Column("seller_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("body", sa.Text),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ---- audit / settings ----
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(60)),
        sa.Column("resource_id", sa.String(64)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"), index=True),
    )

    op.create_table(
        "site_settings",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value", sa.Text),
        sa.Column("description", sa.String(255)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("site_settings")
    op.drop_table("audit_logs")
    op.drop_table("reviews")
    op.drop_table("payments")
    op.drop_table("user_promotions")
    op.drop_table("promotion_packages")
    op.drop_table("reports")
    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
    op.drop_table("favorites")
    op.drop_table("car_features")
    op.drop_table("car_videos")
    op.drop_table("car_images")
    op.drop_table("cars")
    op.drop_table("dealer_employees")
    op.drop_table("dealers")
    op.drop_table("models")
    op.drop_table("makes")
    op.drop_table("locations")
    op.drop_table("categories")
    op.drop_table("email_verification_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    op.drop_table("permissions")
    op.drop_table("users")