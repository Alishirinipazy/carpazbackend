"""merge contracts and inspection sheet images

Revision ID: b8ed42e4f387
Revises: 4d798d47472a, e5f6a7b8c9d0
Create Date: 2026-09-11 17:17:00.533265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8ed42e4f387'
down_revision: Union[str, None] = ('4d798d47472a', 'e5f6a7b8c9d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
