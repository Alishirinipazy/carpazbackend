"""add sheet_images to car_inspections

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-06 00:00:00

Adds an optional list of uploaded scan/photo filenames for the کارشناسی
report, for when the admin wants to attach the paper form itself (or extra
photos) instead of / in addition to filling the graphical checklist.
See app/models/inspection.py.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL does not allow a DEFAULT clause on JSON columns (error 1101) -
    # add it nullable first, backfill existing rows with an empty array,
    # then tighten to NOT NULL once every row has a value.
    op.add_column(
        "car_inspections",
        sa.Column("sheet_images", sa.JSON(), nullable=True),
    )
    op.execute("UPDATE car_inspections SET sheet_images = JSON_ARRAY() WHERE sheet_images IS NULL")
    op.alter_column("car_inspections", "sheet_images", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    op.drop_column("car_inspections", "sheet_images")
