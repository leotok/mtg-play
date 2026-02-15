from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base
from app.models.game import TurnPhase, CardZone


class GameState(Base):
    __tablename__ = "game_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_room_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_rooms.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_turn: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    current_phase: Mapped[TurnPhase] = mapped_column(String, nullable=False, default=TurnPhase.UNTAP)
    starting_player_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    game_room: Mapped["GameRoom"] = relationship("GameRoom", back_populates="game_state")
    players: Mapped[list["PlayerGameState"]] = relationship("PlayerGameState", back_populates="game_state", cascade="all, delete-orphan")
    cards: Mapped[list["GameCard"]] = relationship("GameCard", back_populates="game_state", cascade="all, delete-orphan")


class PlayerGameState(Base):
    __tablename__ = "player_game_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_state_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_states.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    player_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    life_total: Mapped[int] = mapped_column(Integer, default=40)
    poison_counters: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game_state: Mapped["GameState"] = relationship("GameState", back_populates="players")
    user: Mapped["User"] = relationship("User")
    cards: Mapped[list["GameCard"]] = relationship("GameCard", back_populates="player_state")


class GameCard(Base):
    __tablename__ = "game_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_state_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_states.id", ondelete="CASCADE"), nullable=False)
    player_game_state_id: Mapped[int] = mapped_column(Integer, ForeignKey("player_game_states.id", ondelete="CASCADE"), nullable=False)
    deck_card_id: Mapped[int] = mapped_column(Integer, ForeignKey("deck_cards.id"), nullable=True)
    
    card_scryfall_id: Mapped[str] = mapped_column(String, nullable=False)
    card_name: Mapped[str] = mapped_column(String, nullable=False)
    mana_cost: Mapped[str | None] = mapped_column(String, nullable=True)
    cmc: Mapped[float | None] = mapped_column(Float, nullable=True)
    type_line: Mapped[str | None] = mapped_column(String, nullable=True)
    oracle_text: Mapped[str | None] = mapped_column(String, nullable=True)
    colors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    power: Mapped[str | None] = mapped_column(String, nullable=True)
    toughness: Mapped[str | None] = mapped_column(String, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)
    image_uris: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    card_faces: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    
    zone: Mapped[CardZone] = mapped_column(String, nullable=False, default=CardZone.LIBRARY)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    is_tapped: Mapped[bool] = mapped_column(Boolean, default=False)
    is_face_up: Mapped[bool] = mapped_column(Boolean, default=True)
    battlefield_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    battlefield_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    is_attacking: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=False)
    damage_received: Mapped[int] = mapped_column(Integer, default=0)

    game_state: Mapped["GameState"] = relationship("GameState", back_populates="cards")
    player_state: Mapped["PlayerGameState"] = relationship("PlayerGameState", back_populates="cards")
