"""add car_models, car_trims and Car.car_model_id/car_trim_id

Revision ID: 8b3f1c6e9a2d
Revises: 4d798d47472a
Create Date: 2026-09-12 00:00:00

ساختار درختی برند → مدل → تیریم برای انتخاب «مدل خودرو» از یک فهرست
قابل‌جستجو به‌جای تایپ آزاد. See app/models/car_catalog.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8b3f1c6e9a2d"
down_revision: Union[str, None] = "4d798d47472a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "car_models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_car_models_brand_id", "car_models", ["brand_id"])

    op.create_table(
        "car_trims",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("car_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_car_trims_model_id", "car_trims", ["model_id"])

    op.add_column("cars", sa.Column("car_model_id", sa.Integer(), sa.ForeignKey("car_models.id", ondelete="SET NULL"), nullable=True))
    op.add_column("cars", sa.Column("car_trim_id", sa.Integer(), sa.ForeignKey("car_trims.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_cars_car_model_id", "cars", ["car_model_id"])
    op.create_index("ix_cars_car_trim_id", "cars", ["car_trim_id"])


def downgrade() -> None:
    op.drop_index("ix_cars_car_trim_id", table_name="cars")
    op.drop_index("ix_cars_car_model_id", table_name="cars")
    op.drop_column("cars", "car_trim_id")
    op.drop_column("cars", "car_model_id")
    op.drop_table("car_trims")
    op.drop_table("car_models")
