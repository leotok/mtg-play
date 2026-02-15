"""add game state tables

Revision ID: 5f1265c61b9a
Revises: 44cbe43b562f
Create Date: 2026-02-14 23:01:24.380163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f1265c61b9a'
down_revision: Union[str, Sequence[str], None] = '44cbe43b562f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('game_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_room_id', sa.Integer(), nullable=False),
    sa.Column('current_turn', sa.Integer(), nullable=False),
    sa.Column('active_player_id', sa.Integer(), nullable=False),
    sa.Column('current_phase', sa.String(), nullable=False),
    sa.Column('starting_player_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['active_player_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['game_room_id'], ['game_rooms.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['starting_player_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('game_room_id')
    )
    op.create_index(op.f('ix_game_states_id'), 'game_states', ['id'], unique=False)
    op.create_table('player_game_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_state_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('player_order', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('life_total', sa.Integer(), nullable=False),
    sa.Column('poison_counters', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['game_state_id'], ['game_states.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_game_states_id'), 'player_game_states', ['id'], unique=False)
    op.create_table('game_cards',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_state_id', sa.Integer(), nullable=False),
    sa.Column('player_game_state_id', sa.Integer(), nullable=False),
    sa.Column('deck_card_id', sa.Integer(), nullable=True),
    sa.Column('card_scryfall_id', sa.String(), nullable=False),
    sa.Column('card_name', sa.String(), nullable=False),
    sa.Column('mana_cost', sa.String(), nullable=True),
    sa.Column('cmc', sa.Float(), nullable=True),
    sa.Column('type_line', sa.String(), nullable=True),
    sa.Column('oracle_text', sa.String(), nullable=True),
    sa.Column('colors', sa.JSON(), nullable=True),
    sa.Column('power', sa.String(), nullable=True),
    sa.Column('toughness', sa.String(), nullable=True),
    sa.Column('keywords', sa.JSON(), nullable=True),
    sa.Column('image_uris', sa.JSON(), nullable=True),
    sa.Column('card_faces', sa.JSON(), nullable=True),
    sa.Column('zone', sa.String(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('is_tapped', sa.Boolean(), nullable=False),
    sa.Column('is_face_up', sa.Boolean(), nullable=False),
    sa.Column('battlefield_x', sa.Float(), nullable=True),
    sa.Column('battlefield_y', sa.Float(), nullable=True),
    sa.Column('is_attacking', sa.Boolean(), nullable=False),
    sa.Column('is_blocking', sa.Boolean(), nullable=False),
    sa.Column('damage_received', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['deck_card_id'], ['deck_cards.id'], ),
    sa.ForeignKeyConstraint(['game_state_id'], ['game_states.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['player_game_state_id'], ['player_game_states.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_cards_id'), 'game_cards', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_game_cards_id'), table_name='game_cards')
    op.drop_table('game_cards')
    op.drop_index(op.f('ix_player_game_states_id'), table_name='player_game_states')
    op.drop_table('player_game_states')
    op.drop_index(op.f('ix_game_states_id'), table_name='game_states')
    op.drop_table('game_states')
