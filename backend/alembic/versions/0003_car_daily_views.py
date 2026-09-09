"""add car_daily_views table

Revision ID: 0003_car_daily_views
Revises: 0002_car_contact
Create Date: 2026-09-08

Adds a per-day view counter table so sellers can see how many people
viewed their listing on a given day, instead of only the lifetime total
on ``cars.views_count``.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_car_daily_views"
down_revision = "0002_car_contact"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "car_daily_views",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("car_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("view_date", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("car_id", "view_date", name="uq_car_daily_view"),
    )
    op.create_index("ix_car_daily_views_car_id", "car_daily_views", ["car_id"])
    op.create_index("ix_car_daily_views_view_date", "car_daily_views", ["view_date"])


def downgrade() -> None:
    op.drop_index("ix_car_daily_views_view_date", table_name="car_daily_views")
    op.drop_index("ix_car_daily_views_car_id", table_name="car_daily_views")
    op.drop_table("car_daily_views")
