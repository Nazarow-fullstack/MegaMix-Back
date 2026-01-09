"""Add purchase to expensecategory

Revision ID: c4a4eee0a5cc
Revises: 9b9ac17c2b1d
Create Date: 2026-01-09 22:07:12.121450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a4eee0a5cc'
down_revision: Union[str, Sequence[str], None] = '9b9ac17c2b1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE expensecategory ADD VALUE 'purchase'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
