"""add mana pool fields

Revision ID: 5d395a334f2c
Revises: add_game_mode
Create Date: 2026-03-02 00:14:58.526971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d395a334f2c'
down_revision: Union[str, Sequence[str], None] = 'add_game_mode'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('player_game_states', sa.Column('white_mana', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_game_states', sa.Column('blue_mana', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_game_states', sa.Column('black_mana', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_game_states', sa.Column('red_mana', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_game_states', sa.Column('green_mana', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('player_game_states', sa.Column('colorless_mana', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('player_game_states', 'colorless_mana')
    op.drop_column('player_game_states', 'green_mana')
    op.drop_column('player_game_states', 'red_mana')
    op.drop_column('player_game_states', 'black_mana')
    op.drop_column('player_game_states', 'blue_mana')
    op.drop_column('player_game_states', 'white_mana')
