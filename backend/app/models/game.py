from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
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


class GameRoom(Base):
    __tablename__ = "game_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    is_public = Column(Boolean, default=False)
    max_players = Column(Integer, nullable=False, default=4)
    power_bracket = Column(SQLEnum(PowerBracket), nullable=False, default=PowerBracket.CASUAL)
    status = Column(SQLEnum(GameStatus), nullable=False, default=GameStatus.WAITING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    host = relationship("User", foreign_keys=[host_id])
    players = relationship("GameRoomPlayer", back_populates="game_room", cascade="all, delete-orphan")


class GameRoomPlayer(Base):
    __tablename__ = "game_room_players"

    id = Column(Integer, primary_key=True, index=True)
    game_room_id = Column(Integer, ForeignKey("game_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(PlayerStatus), nullable=False, default=PlayerStatus.PENDING)
    is_host = Column(Boolean, default=False)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game_room = relationship("GameRoom", back_populates="players")
    user = relationship("User")
    deck = relationship("Deck")
