from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class PowerBracket(str, enum.Enum):
    PRECON = "precon"
    CASUAL = "casual"
    OPTIMIZED = "optimized"
    CEDH = "cedh"


class GameStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PlayerStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TurnPhase(str, enum.Enum):
    UNTAP = "untap"
    UPKEEP = "upkeep"
    DRAW = "draw"
    MAIN1 = "main1"
    COMBAT_START = "combat_start"
    COMBAT_ATTACK = "combat_attack"
    COMBAT_BLOCK = "combat_block"
    COMBAT_DAMAGE = "combat_damage"
    COMBAT_END = "combat_end"
    MAIN2 = "main2"
    END = "end"
    CLEANUP = "cleanup"


class CardZone(str, enum.Enum):
    LIBRARY = "library"
    HAND = "hand"
    BATTLEFIELD = "battlefield"
    GRAVEYARD = "graveyard"
    EXILE = "exile"
    COMMANDER = "commander"


class GameRoom(Base):
    __tablename__ = "game_rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    max_players: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    power_bracket: Mapped[PowerBracket] = mapped_column(SQLEnum(PowerBracket), nullable=False, default=PowerBracket.CASUAL)
    status: Mapped[GameStatus] = mapped_column(SQLEnum(GameStatus), nullable=False, default=GameStatus.WAITING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    host: Mapped["User"] = relationship("User", foreign_keys=[host_id])
    players: Mapped[list["GameRoomPlayer"]] = relationship("GameRoomPlayer", back_populates="game_room", cascade="all, delete-orphan")
    game_state: Mapped["GameState"] = relationship("GameState", back_populates="game_room", uselist=False)


class GameRoomPlayer(Base):
    __tablename__ = "game_room_players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_room_id: Mapped[int] = mapped_column(Integer, ForeignKey("game_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[PlayerStatus] = mapped_column(SQLEnum(PlayerStatus), nullable=False, default=PlayerStatus.PENDING)
    is_host: Mapped[bool] = mapped_column(Boolean, default=False)
    deck_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("decks.id"), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    game_room: Mapped["GameRoom"] = relationship("GameRoom", back_populates="players")
    user: Mapped["User"] = relationship("User")
    deck: Mapped["Deck | None"] = relationship("Deck")
