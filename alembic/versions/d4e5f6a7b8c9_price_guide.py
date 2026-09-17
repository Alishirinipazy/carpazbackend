"""add price_guide_entries table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-04 00:00:00

"قیمت روز خودرو" - جدول مرجع قیمت بازار/نمایندگی خودروها (صفر/کارکرده).
See app/models/price_guide.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "price_guide_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand", sa.String(255), nullable=False),
        sa.Column("model", sa.String(255), nullable=False),
        sa.Column("trim", sa.String(255), nullable=True),
        sa.Column("year", sa.String(32), nullable=True),
        sa.Column("condition", sa.SmallInteger(), nullable=False),
        sa.Column("market_price", sa.BigInteger(), nullable=True),
        sa.Column("agency_price", sa.BigInteger(), nullable=True),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_price_guide_entries_brand", "price_guide_entries", ["brand"])
    op.create_index("ix_price_guide_entries_model", "price_guide_entries", ["model"])
    op.create_index("ix_price_guide_entries_condition", "price_guide_entries", ["condition"])


def downgrade() -> None:
    op.drop_table("price_guide_entries")
