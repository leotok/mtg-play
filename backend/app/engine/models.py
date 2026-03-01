from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


class TurnPhase(str, Enum):
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


class CardZone(str, Enum):
    LIBRARY = "library"
    HAND = "hand"
    BATTLEFIELD = "battlefield"
    GRAVEYARD = "graveyard"
    EXILE = "exile"
    COMMANDER = "commander"
    STACK = "stack"


class ManaColor(str, Enum):
    WHITE = "white"
    BLUE = "blue"
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    COLORLESS = "colorless"


class CardPosition(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None


class Card(BaseModel):
    id: int
    card_scryfall_id: str
    card_name: str
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    keywords: Optional[List[str]] = None
    image_uris: Optional[Dict] = None
    card_faces: Optional[List[Dict]] = None
    
    zone: CardZone
    position: int
    
    is_tapped: bool = False
    is_face_up: bool = True
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None
    
    is_attacking: bool = False
    is_blocking: bool = False
    is_summoning_sick: bool = True
    damage_received: int = 0
    
    player_id: int


class PlayerState(BaseModel):
    id: int
    user_id: int
    username: str
    player_order: int
    is_active: bool
    life_total: int = 40
    poison_counters: int = 0
    commander_damage: Dict[int, int] = Field(default_factory=dict)
    mana_pool: Dict[ManaColor, int] = Field(default_factory=dict)
    
    library: List[Card] = Field(default_factory=list)
    hand: List[Card] = Field(default_factory=list)
    battlefield: List[Card] = Field(default_factory=list)
    graveyard: List[Card] = Field(default_factory=list)
    exile: List[Card] = Field(default_factory=list)
    commander: List[Card] = Field(default_factory=list)


class GameStateData(BaseModel):
    id: int
    game_room_id: int
    current_turn: int
    active_player_id: int
    active_player_username: str
    current_phase: TurnPhase
    starting_player_id: int
    players: List[PlayerState]
    created_at: datetime


class ActionResult(BaseModel):
    success: bool = True
    message: Optional[str] = None
    game_state: Optional[GameStateData] = None
    affected_cards: List[int] = Field(default_factory=list)
    phase_changed: bool = False
    turn_changed: bool = False
    new_phase: Optional[TurnPhase] = None
    new_turn: Optional[int] = None
    new_active_player: Optional[int] = None


class MoveCardInput(BaseModel):
    card_id: int
    target_zone: CardZone
    position: int = 0
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None


class CastSpellInput(BaseModel):
    card_id: int
    target_zone: CardZone = CardZone.BATTLEFIELD
    position: int = 0
    battlefield_x: Optional[float] = None
    battlefield_y: Optional[float] = None
    x_value: Optional[int] = None
    targets: List[int] = Field(default_factory=list)
    modes: List[int] = Field(default_factory=list)


class DeclareAttackerInput(BaseModel):
    card_id: int
    target_player_id: Optional[int] = None


class DeclareBlockerInput(BaseModel):
    attacker_id: int
    blocker_id: int


class ActivateAbilityInput(BaseModel):
    card_id: int
    ability_index: int
    targets: List[int] = Field(default_factory=list)
    mode: Optional[int] = None
    x_value: Optional[int] = None


def card_to_engine(card, player_id: int) -> Card:
    return Card(
        id=card.id,
        card_scryfall_id=card.card_scryfall_id,
        card_name=card.card_name,
        mana_cost=card.mana_cost,
        cmc=card.cmc,
        type_line=card.type_line,
        oracle_text=card.oracle_text,
        colors=card.colors,
        power=card.power,
        toughness=card.toughness,
        keywords=card.keywords,
        image_uris=card.image_uris,
        card_faces=card.card_faces,
        zone=card.zone,
        position=card.position,
        is_tapped=card.is_tapped,
        is_face_up=card.is_face_up,
        battlefield_x=card.battlefield_x,
        battlefield_y=card.battlefield_y,
        is_attacking=card.is_attacking,
        is_blocking=card.is_blocking,
        is_summoning_sick=False,
        damage_received=card.damage_received,
        player_id=player_id,
    )
