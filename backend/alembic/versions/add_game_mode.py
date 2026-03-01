"""Add game_mode to game_rooms

Revision ID: add_game_mode
Revises: efb7ab788b45
Create Date: 2026-02-28 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_game_mode'
down_revision: Union[str, Sequence[str], None] = 'efb7ab788b45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('game_rooms', 
        sa.Column('game_mode', sa.String(), nullable=False, server_default='MANUAL')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('game_rooms', 'game_mode')
