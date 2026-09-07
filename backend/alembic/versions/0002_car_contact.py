"""add car contact preferences

Revision ID: 0002_car_contact
Revises: 0001_initial
Create Date: 2026-09-04

Adds phone_country_code, phone_number, and contact_methods columns to the
``cars`` table so sellers can publish how they want buyers to reach them
(phone, WhatsApp, Viber, Telegram, or in-app chat).
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_car_contact"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cars", sa.Column("phone_country_code", sa.String(length=8), nullable=True))
    op.add_column("cars", sa.Column("phone_number", sa.String(length=40), nullable=True))
    op.add_column(
        "cars",
        sa.Column("contact_methods", sa.String(length=120), nullable=True, server_default="PHONE,CHAT"),
    )


def downgrade() -> None:
    op.drop_column("cars", "contact_methods")
    op.drop_column("cars", "phone_number")
    op.drop_column("cars", "phone_country_code")