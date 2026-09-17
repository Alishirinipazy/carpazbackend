"""add sheet_images to car_inspections

Revision ID: 2f6a4c8e1b7d
Revises: 8b3f1c6e9a2d
Create Date: 2026-09-13 00:00:00

عکس‌های اسکن/عکاسی‌شده از برگه‌ی فیزیکی کارشناسی - مکمل چک‌لیست دیجیتال
موجود (ستون items). See app/models/inspection.py.

⚠️ اگه این ستون از قبل روی دیتابیستون دستی اضافه شده (مثلاً موقع دیباگ)،
این مایگریشن رو upgrade نکنید - به‌جاش فقط:
    alembic stamp 2f6a4c8e1b7d
بزنید تا Alembic بدون اجرای دوباره‌ی ALTER TABLE، این نسخه رو "دیده‌شده"
علامت بزنه.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "2f6a4c8e1b7d"
down_revision: Union[str, None] = "8b3f1c6e9a2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("car_inspections", sa.Column("sheet_images", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("car_inspections", "sheet_images")
