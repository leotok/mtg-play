"""Add game tables

Revision ID: 145128b0a162
Revises: 7bcee0718405
Create Date: 2026-02-13 18:40:38.703641

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '145128b0a162'
down_revision: Union[str, Sequence[str], None] = '7bcee0718405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('game_rooms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('host_id', sa.Integer(), nullable=False),
    sa.Column('invite_code', sa.String(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('max_players', sa.Integer(), nullable=False),
    sa.Column('power_bracket', sa.Enum('PRECON', 'CASUAL', 'OPTIMIZED', 'CEDH', name='powerbracket'), nullable=False),
    sa.Column('status', sa.Enum('WAITING', 'IN_PROGRESS', 'COMPLETED', name='gamestatus'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_rooms_id'), 'game_rooms', ['id'], unique=False)
    op.create_index(op.f('ix_game_rooms_invite_code'), 'game_rooms', ['invite_code'], unique=True)
    op.create_table('game_room_players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_room_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'REJECTED', name='playerstatus'), nullable=False),
    sa.Column('is_host', sa.Boolean(), nullable=True),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['game_room_id'], ['game_rooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_room_players_id'), 'game_room_players', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_game_room_players_id'), table_name='game_room_players')
    op.drop_table('game_room_players')
    op.drop_index(op.f('ix_game_rooms_invite_code'), table_name='game_rooms')
    op.drop_index(op.f('ix_game_rooms_id'), table_name='game_rooms')
    op.drop_table('game_rooms')
