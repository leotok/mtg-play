from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from app.models.game import TurnPhase, CardZone


class GameLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    player_id: int
    action_type: str
    card_id: Optional[int] = None
    card_name: Optional[str] = None
    from_zone: Optional[str] = None
    to_zone: Optional[str] = None
    message: str
    created_at: datetime


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
    position: int


class PlayerGameStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    player_order: int
    is_active: bool
    life_total: int
    poison_counters: int
    mana_pool: Optional[Dict[str, int]] = {}
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
    logs: Optional[List[GameLogResponse]] = []
    game_mode: Optional[str] = None


class DrawCardRequest(BaseModel):
    card_id: Optional[int] = None


class PlayCardRequest(BaseModel):
    card_id: int
    target_zone: CardZone = CardZone.BATTLEFIELD
    position: int = 0
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None
    side_index: Optional[int] = None


class MoveCardRequest(BaseModel):
    card_id: int
    target_zone: CardZone
    position: int = 0


class MoveCardsRequest(BaseModel):
    cards: List[MoveCardRequest]


class TapCardRequest(BaseModel):
    card_id: int


class BattlefieldPositionRequest(BaseModel):
    card_id: int
    x: float
    y: float


class AdjustLifeRequest(BaseModel):
    amount: int


class AddManaRequest(BaseModel):
    color: str
    amount: int = 1


class TapLandForManaRequest(BaseModel):
    """Request to tap a land and add mana to the pool."""
    color: Optional[str] = None  # Required for hybrid lands, optional for single color lands


class GameActionErrorResponse(BaseModel):
    error_type: str
    message: str
    code: str


class CardSideOption(BaseModel):
    side_index: int
    name: str
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    image_url: Optional[str] = None


class ChooseCardSideResponse(BaseModel):
    card_id: int
    card_name: str
    sides: List[CardSideOption]
    requires_side_selection: bool = True


class ValidPlayCard(BaseModel):
    card_id: int
    card_name: str
    zone: CardZone
    mana_cost: Optional[str] = None
    can_afford_mana: bool
    needs_side_selection: bool = False
    sides: Optional[List[CardSideOption]] = None


class ValidPlaysResponse(BaseModel):
    current_phase: TurnPhase
    can_cast_spells: bool
    can_play_land: bool
    available_mana: Dict[str, int]
    untapped_lands_count: int
    plays: List[ValidPlayCard]
