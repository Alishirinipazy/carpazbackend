"""add car_inspections table

Revision ID: b7c9d1e2f3a4
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 00:00:00

Adds the کارشناسی (expert inspection) report - one per car, admin-filled,
shown on the car's product page. See app/models/inspection.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c9d1e2f3a4"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "car_inspections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expert_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("vehicle_type", sa.String(255), nullable=False, server_default=""),
        sa.Column("color", sa.String(64), nullable=False, server_default=""),
        sa.Column("model", sa.String(255), nullable=False, server_default=""),
        sa.Column("client_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("chassis_number", sa.String(64), nullable=False, server_default=""),
        sa.Column("plate_number", sa.String(32), nullable=False, server_default=""),
        sa.Column("inspection_date", sa.Date(), nullable=True),
        sa.Column("mileage_km", sa.Integer(), nullable=True),
        sa.Column("visit_time", sa.String(32), nullable=False, server_default=""),
        sa.Column("visit_location", sa.String(255), nullable=False, server_default=""),
        sa.Column("suggested_price", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("car_id", name="uq_car_inspections_car_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("car_inspections")
