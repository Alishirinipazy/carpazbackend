"""merge heads

Revision ID: e864bfc7692e
Revises: 8b3f1c6e9a2d, b8ed42e4f387
Create Date: 2026-09-12 16:20:53.996368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e864bfc7692e'
down_revision: Union[str, None] = ('8b3f1c6e9a2d', 'b8ed42e4f387')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
