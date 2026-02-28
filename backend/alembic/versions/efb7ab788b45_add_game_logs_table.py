"""Add game_logs table

Revision ID: efb7ab788b45
Revises: 5f1265c61b9a
Create Date: 2026-02-28 00:53:44.329520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efb7ab788b45'
down_revision: Union[str, Sequence[str], None] = '5f1265c61b9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('game_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('action_type', sa.String(), nullable=False),
    sa.Column('card_id', sa.Integer(), nullable=True),
    sa.Column('card_name', sa.String(), nullable=True),
    sa.Column('from_zone', sa.String(), nullable=True),
    sa.Column('to_zone', sa.String(), nullable=True),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['game_states.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_logs_id'), 'game_logs', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_game_logs_id'), table_name='game_logs')
    op.drop_table('game_logs')
