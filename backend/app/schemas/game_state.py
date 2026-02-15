from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.game import TurnPhase, CardZone


class GameCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_scryfall_id: str
    card_name: str
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[list] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    keywords: Optional[list] = None
    image_uris: Optional[dict] = None
    card_faces: Optional[list] = None
    zone: CardZone
    position: int
    is_tapped: bool
    is_face_up: bool
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None
    is_attacking: bool
    is_blocking: bool
    damage_received: int


class GameCardInBattlefieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_scryfall_id: str
    card_name: str
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uris: Optional[dict] = None
    card_faces: Optional[list] = None
    is_tapped: bool
    is_face_up: bool
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None
    is_attacking: bool
    is_blocking: bool


class PlayerGameStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    player_order: int
    is_active: bool
    life_total: int
    poison_counters: int
    library: List[GameCardResponse]
    hand: List[GameCardResponse]
    battlefield: List[GameCardInBattlefieldResponse]
    graveyard: List[GameCardResponse]
    exile: List[GameCardResponse]
    commander: List[GameCardResponse]


class GameStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_room_id: int
    current_turn: int
    active_player_id: int
    active_player_username: str
    current_phase: TurnPhase
    starting_player_id: int
    players: List[PlayerGameStateResponse]
    created_at: datetime


class DrawCardRequest(BaseModel):
    card_id: Optional[int] = None


class PlayCardRequest(BaseModel):
    card_id: int
    target_zone: CardZone = CardZone.BATTLEFIELD
    position: int = 0


class MoveCardRequest(BaseModel):
    card_id: int
    target_zone: CardZone
    position: int = 0


class TapCardRequest(BaseModel):
    card_id: int


class BattlefieldPositionRequest(BaseModel):
    card_id: int
    x: float
    y: float
