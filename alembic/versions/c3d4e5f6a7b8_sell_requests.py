"""add sell_requests table

Revision ID: c3d4e5f6a7b8
Revises: b7c9d1e2f3a4
Create Date: 2026-08-30 00:00:00

Backs the "فروش ماشین شما" (sell your car) lead form - a visitor tells us
about a car they want to sell to the dealership; a sales agent calls them
back. See app/models/sell_request.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b7c9d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sell_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("car_type", sa.String(255), nullable=False),
        sa.Column("car_model", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        # 0 pending, 1 contacted, 2 accepted, 3 rejected
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("sell_requests")
