"""add lands_played_this_turn

Revision ID: cdc2c22e0fb7
Revises: 5d395a334f2c
Create Date: 2026-03-03 00:18:33.657575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdc2c22e0fb7'
down_revision: Union[str, Sequence[str], None] = '5d395a334f2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('player_game_states', sa.Column('lands_played_this_turn', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('player_game_states', 'lands_played_this_turn')
