from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.game import PowerBracket, GameStatus, PlayerStatus


class DeckInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    commander_name: Optional[str] = None
    commander_image_uris: Optional[dict] = None


class GameRoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False
    max_players: int = Field(default=4, ge=2, le=4)
    power_bracket: PowerBracket = PowerBracket.CASUAL


class GameRoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    max_players: Optional[int] = Field(None, ge=2, le=4)
    power_bracket: Optional[PowerBracket] = None


class DeckSelectionRequest(BaseModel):
    deck_id: int


class GameRoomPlayerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    status: PlayerStatus
    is_host: bool
    deck_id: Optional[int] = None
    deck: Optional[DeckInfo] = None
    joined_at: datetime


class GameRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    host_id: int
    host_username: str
    invite_code: str
    is_public: bool
    max_players: int
    power_bracket: PowerBracket
    status: GameStatus
    players: List[GameRoomPlayerResponse]
    created_at: datetime


class GameRoomListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    host_username: str
    is_public: bool
    max_players: int
    current_players: int
    power_bracket: PowerBracket
    status: GameStatus
    created_at: datetime
    is_in_game: bool = False


class JoinResponse(BaseModel):
    message: str
    game_room: Optional[GameRoomResponse] = None
