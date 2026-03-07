from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Set, Tuple
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


MANA_SYMBOL_MAP = {
    "W": ManaColor.WHITE,
    "U": ManaColor.BLUE,
    "B": ManaColor.BLACK,
    "R": ManaColor.RED,
    "G": ManaColor.GREEN,
    "C": ManaColor.COLORLESS,
}

GENERIC_KEY = "generic"


def parse_mana_cost(mana_cost: Optional[str]) -> Tuple[Dict[ManaColor, int], List[Set[ManaColor]]]:
    """Parse a MTG mana cost string into a dictionary of color amounts and hybrid options.
    
    Returns:
        Tuple of (regular_mana, hybrid_options)
        - regular_mana: Dict mapping ManaColor to amount needed
        - hybrid_options: List of sets representing hybrid/payment alternatives
        
    Examples:
        "{W}{U}{2}" -> ({WHITE: 1, BLUE: 1, COLORLESS: 2}, [])
        "{3}{R}{R}" -> ({COLORLESS: 3, RED: 2}, [])
        "{B/R}" -> ({}, [{BLACK, RED}])
        "{2}{B/R}" -> ({COLORLESS: 2}, [{BLACK, RED}])
        "{W/P}" -> ({}, [{WHITE}])  # phyrexian - can pay white OR 1 life
        None or "" -> ({}, [])
    """
    if not mana_cost:
        return ({}, [])
    
    result: Dict[ManaColor, int] = {}
    hybrid_options: List[Set[ManaColor]] = []
    
    import re
    symbols = re.findall(r'\{[^}]+\}', mana_cost)
    
    for symbol in symbols:
        symbol = symbol.strip('{}')
        
        if symbol.isdigit():
            result[GENERIC_KEY] = result.get(GENERIC_KEY, 0) + int(symbol)
        elif symbol in MANA_SYMBOL_MAP:
            color = MANA_SYMBOL_MAP[symbol]
            result[color] = result.get(color, 0) + 1
        elif symbol == "X" or symbol == "XRR" or symbol.startswith("X"):
            pass
        elif "/" in symbol:
            parts = symbol.split("/")
            hybrid_colors: Set[ManaColor] = set()
            
            for part in parts:
                if part in MANA_SYMBOL_MAP:
                    color = MANA_SYMBOL_MAP[part]
                    hybrid_colors.add(color)
                elif part.isdigit():
                    hybrid_colors.add(int(part))
            
            hybrid_options.append(hybrid_colors)
    
    return (result, hybrid_options)


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
    
    played_as_side: Optional[int] = None
    
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
    lands_played_this_turn: int = 0
    
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
        played_as_side=card.played_as_side if hasattr(card, 'played_as_side') else None,
    )


def get_card_face_mana_cost(card: Card, side_index: int) -> Optional[str]:
    """Extract mana cost from a specific card face."""
    if not card.card_faces or len(card.card_faces) <= side_index:
        return None
    face = card.card_faces[side_index]
    return face.get("mana_cost") if isinstance(face, dict) else getattr(face, "mana_cost", None)


def get_mana_cost_for_card(card: Card) -> Tuple[Dict[ManaColor, int], List[Set[ManaColor]]]:
    """Get the mana cost for a card, considering DFC sides."""
    if card.played_as_side is not None:
        mana_cost = get_card_face_mana_cost(card, card.played_as_side)
    elif card.card_faces:
        mana_cost = get_card_face_mana_cost(card, 0)
    else:
        mana_cost = card.mana_cost
    
    return parse_mana_cost(mana_cost)


def card_needs_side_selection(card: Card) -> bool:
    """Check if a card needs side selection (DFC with multiple non-empty mana costs)."""
    if not card.card_faces or len(card.card_faces) < 2:
        return False
    
    mana_costs = []
    for face in card.card_faces:
        if isinstance(face, dict):
            mc = face.get("mana_cost")
        else:
            mc = getattr(face, "mana_cost", None)
        mana_costs.append(mc)
    
    has_front_cost = mana_costs[0] and mana_costs[0] != ""
    has_back_cost = len(mana_costs) > 1 and mana_costs[1] and mana_costs[1] != ""
    
    return has_front_cost and has_back_cost


def get_card_sides_info(card: Card) -> List[Dict]:
    """Get information about all card sides for side selection."""
    if not card.card_faces:
        return []
    
    sides = []
    for i, face in enumerate(card.card_faces):
        if isinstance(face, dict):
            name = face.get("name", f"Side {i + 1}")
            mana_cost = face.get("mana_cost")
            type_line = face.get("type_line")
            image_uris = face.get("image_uris")
        else:
            name = getattr(face, "name", f"Side {i + 1}")
            mana_cost = getattr(face, "mana_cost", None)
            type_line = getattr(face, "type_line", None)
            image_uris = getattr(face, "image_uris", None)
        
        image_url = None
        if image_uris:
            image_url = image_uris.get("normal") or image_uris.get("large") or image_uris.get("small")
        elif card.image_uris:
            image_url = card.image_uris.get("normal") or card.image_uris.get("large") or card.image_uris.get("small")
        
        sides.append({
            "side_index": i,
            "name": name,
            "mana_cost": mana_cost,
            "type_line": type_line,
            "image_url": image_url,
        })
    
    return sides
