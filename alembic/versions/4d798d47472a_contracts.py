"""add contracts table

Revision ID: 4d798d47472a
Revises: d4e5f6a7b8c9
Create Date: 2026-09-08 00:00:00

مبایعه‌نامه‌ی خرید و فروش خودرو. See app/models/contract.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4d798d47472a"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contract_date", sa.Date(), nullable=True),
        sa.Column("price", sa.BigInteger(), nullable=True),
        sa.Column("price_text", sa.String(500), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_contracts_car_id", "contracts", ["car_id"])


def downgrade() -> None:
    op.drop_table("contracts")
