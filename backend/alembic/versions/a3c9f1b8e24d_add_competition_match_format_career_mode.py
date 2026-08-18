"""add competition, match_format, career_mode, series_length to careers

Revision ID: a3c9f1b8e24d
Revises: 1f907d4233cc
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c9f1b8e24d'
down_revision: Union[str, Sequence[str], None] = '1f907d4233cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('careers', sa.Column('competition', sa.String(), nullable=False, server_default='ipl'))
    op.add_column('careers', sa.Column('match_format', sa.String(), nullable=False, server_default='t20'))
    op.add_column('careers', sa.Column('career_mode', sa.String(), nullable=False, server_default='league'))
    op.add_column('careers', sa.Column('series_length', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('careers', 'series_length')
    op.drop_column('careers', 'career_mode')
    op.drop_column('careers', 'match_format')
    op.drop_column('careers', 'competition')
