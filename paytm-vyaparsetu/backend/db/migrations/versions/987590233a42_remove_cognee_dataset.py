"""remove_cognee_dataset

Revision ID: 987590233a42
Revises: 23d3e403cd62
Create Date: 2026-10-06 17:35:55.087752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '987590233a42'
down_revision: Union[str, None] = '23d3e403cd62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('merchants', 'cognee_dataset')


def downgrade() -> None:
    op.add_column('merchants', sa.Column('cognee_dataset', sa.Text(), nullable=True))
