from typing import Optional, TYPE_CHECKING
from app.engine.models import (
    GameStateData,
    PlayerState,
    Card,
    CardZone,
    TurnPhase,
    MoveCardInput,
    CastSpellInput,
    DeclareAttackerInput,
    DeclareBlockerInput,
    ManaColor,
    ActionResult,
    card_to_engine,
)
from app.engine.exceptions import (
    InvalidCardError,
    InvalidPlayerError,
    InvalidZoneError,
    InvalidPhaseError,
    EmptyLibraryError,
)
from app.engine.phases import PhaseManager, create_action_result
from app.engine.actions import CardManager, LifeManager, ManaManager, CombatManager

if TYPE_CHECKING:
    from app.models.game_state import GameState as DBGameState


class GameEngine:
    def __init__(self, game_state: GameStateData):
        self.game_state = game_state
        self.phase_manager = PhaseManager(game_state)
        self.card_manager = CardManager(game_state, self.phase_manager)
        self.life_manager = LifeManager(game_state, self.phase_manager)
        self.mana_manager = ManaManager(game_state, self.phase_manager)
        self.combat_manager = CombatManager(game_state, self.phase_manager)
    
    def get_game_state(self) -> GameStateData:
        return self.game_state
    
    def validate_active_player(self, user_id: int) -> None:
        self.phase_manager.validate_active_player(user_id)
    
    def draw_cards(self, player_id: int, count: int = 1) -> ActionResult:
        try:
            drawn = self.card_manager.draw_cards(player_id, count)
            return create_action_result(
                self.game_state,
                affected_cards=[c.id for c in drawn],
                message=f"Drew {len(drawn)} card(s)",
            )
        except EmptyLibraryError as e:
            raise e
    
    def play_card(
        self,
        card_id: int,
        target_zone: CardZone,
        position: int = 0,
        battlefield_x: Optional[float] = None,
        battlefield_y: Optional[float] = None,
    ) -> ActionResult:
        card = self.card_manager.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        if card.zone not in [CardZone.HAND.value, CardZone.COMMANDER.value]:
            raise InvalidZoneError("Card must be in hand or commander zone to play")
        
        from_zone = CardZone(card.zone)
        
        self.card_manager.move_card(card, target_zone, position)
        
        if battlefield_x is not None:
            card.battlefield_x = battlefield_x
        if battlefield_y is not None:
            card.battlefield_y = battlefield_y
        
        card.is_summoning_sick = True
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"Played {card.card_name} from {from_zone.value}",
        )
    
    def move_card(
        self,
        card_id: int,
        target_zone: CardZone,
        position: int = 0,
        battlefield_x: Optional[float] = None,
        battlefield_y: Optional[float] = None,
    ) -> ActionResult:
        card = self.card_manager.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        from_zone = CardZone(card.zone)
        
        if target_zone in [CardZone.GRAVEYARD, CardZone.EXILE, CardZone.BATTLEFIELD]:
            player = self.phase_manager.get_player_by_id(card.player_id)
            zone_cards = getattr(player, target_zone.value)
            position = len(zone_cards)
        
        if card.zone == CardZone.BATTLEFIELD.value and target_zone != CardZone.BATTLEFIELD:
            if card.is_tapped:
                card.is_tapped = False
        
        self.card_manager.move_card(card, target_zone, position)
        
        if battlefield_x is not None:
            card.battlefield_x = battlefield_x
        if battlefield_y is not None:
            card.battlefield_y = battlefield_y
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"Moved {card.card_name} from {from_zone.value} to {target_zone.value}",
        )
    
    def move_cards(self, card_moves: list[MoveCardInput]) -> ActionResult:
        affected = []
        
        for move in card_moves:
            card = self.card_manager.get_card(move.card_id)
            if not card:
                continue
            
            from_zone = CardZone(card.zone)
            
            target_zone = move.target_zone
            position = move.position
            
            if target_zone in [CardZone.GRAVEYARD, CardZone.EXILE, CardZone.BATTLEFIELD]:
                player = self.phase_manager.get_player_by_id(card.player_id)
                zone_cards = getattr(player, target_zone.value)
                position = len(zone_cards)
            
            if card.zone == CardZone.BATTLEFIELD.value and target_zone != CardZone.BATTLEFIELD:
                if card.is_tapped:
                    card.is_tapped = False
            
            self.card_manager.move_card(card, target_zone, position)
            
            if move.battlefield_x is not None:
                card.battlefield_x = move.battlefield_x
            if move.battlefield_y is not None:
                card.battlefield_y = move.battlefield_y
            
            affected.append(card.id)
        
        card_count = len(affected)
        message = f"Moved {card_count} card(s)"
        
        return create_action_result(
            self.game_state,
            affected_cards=affected,
            message=message,
        )
    
    def tap_card(self, card_id: int) -> ActionResult:
        card = self.card_manager.tap_card(card_id)
        
        action = "untapped" if not card.is_tapped else "tapped"
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"{card.card_name} {action}",
        )
    
    def untap_all(self, player_id: int) -> ActionResult:
        untapped = self.card_manager.untap_all(player_id)
        
        return create_action_result(
            self.game_state,
            affected_cards=[c.id for c in untapped],
            message=f"Untapped {len(untapped)} card(s)",
        )
    
    def update_battlefield_position(
        self,
        card_id: int,
        x: float,
        y: float,
    ) -> ActionResult:
        card = self.card_manager.set_card_position(card_id, x, y)
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"Positioned {card.card_name}",
        )
    
    def pass_priority(self) -> ActionResult:
        next_phase, turn_changed, new_active_player = self.phase_manager.advance_phase()
        
        phase_changed = True
        message = f"Advanced to {next_phase.value.replace('_', ' ').title()}"
        
        if turn_changed:
            message = f"Turn {self.game_state.current_turn} - {next_phase.value.replace('_', ' ').title()}"
            
            player = self.phase_manager.get_current_player()
            for card in player.battlefield:
                card.is_summoning_sick = False
        
        return create_action_result(
            self.game_state,
            phase_changed=phase_changed,
            turn_changed=turn_changed,
            message=message,
        )
    
    def adjust_life(self, player_id: int, amount: int) -> ActionResult:
        player, damage = self.life_manager.adjust_life(player_id, amount)
        
        if amount > 0:
            message = f"{player.username} gained {amount} life"
        else:
            message = f"{player.username} lost {abs(amount)} life"
        
        return create_action_result(
            self.game_state,
            affected_cards=[],
            message=message,
        )
    
    def declare_attacker(
        self,
        card_id: int,
        target_player_id: Optional[int] = None,
    ) -> ActionResult:
        card = self.combat_manager.declare_attacker(card_id, target_player_id)
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"{card.card_name} attacks" + (f" {self._get_player_name(target_player_id)}" if target_player_id else ""),
        )
    
    def declare_blocker(self, attacker_id: int, blocker_id: int) -> ActionResult:
        attacker, blocker = self.combat_manager.declare_blocker(attacker_id, blocker_id)
        
        return create_action_result(
            self.game_state,
            affected_cards=[attacker_id, blocker_id],
            message=f"{blocker.card_name} blocks {attacker.card_name}",
        )
    
    def resolve_combat(self) -> ActionResult:
        damage_events = self.combat_manager.resolve_combat_damage()
        
        for attacker, blocker, damage in damage_events:
            if damage > 0:
                blocker.damage_received += damage
        
        self.combat_manager.clear_combat()
        
        destroyed = self.combat_manager.destroy_dead_creatures()
        
        message = f"Combat resolved. {len(destroyed)} creature(s) destroyed."
        
        return create_action_result(
            self.game_state,
            affected_cards=[c.id for c in destroyed],
            message=message,
        )
    
    def add_mana(self, player_id: int, color: ManaColor, amount: int = 1) -> ActionResult:
        player = self.mana_manager.add_mana(player_id, color, amount)
        
        return create_action_result(
            self.game_state,
            message=f"Added {amount} {color.value} mana to {player.username}'s pool",
        )
    
    def spend_mana(self, player_id: int, **costs: int) -> ActionResult:
        player = self.mana_manager.spend_mana(player_id, **costs)
        
        return create_action_result(
            self.game_state,
            message=f"{player.username} spent mana",
        )
    
    def clear_mana(self, player_id: int) -> ActionResult:
        player = self.mana_manager.clear_mana_pool(player_id)
        
        return create_action_result(
            self.game_state,
            message=f"{player.username}'s mana pool cleared",
        )
    
    def get_player(self, user_id: int):
        return self.phase_manager.get_player_by_id(user_id)
    
    def get_active_player(self):
        return self.phase_manager.get_current_player()
    
    def _get_player_name(self, user_id: Optional[int]) -> str:
        if user_id is None:
            return ""
        try:
            player = self.phase_manager.get_player_by_id(user_id)
            return player.username
        except InvalidPlayerError:
            return ""


def create_engine_from_db(
    db_game_state: "DBGameState",
    db_player_states: list,
    db_cards_by_player: dict,
    usernames: dict,
) -> GameEngine:
    players = []
    
    for ps in db_player_states:
        player_id = ps.user_id
        
        library = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("library", [])]
        hand = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("hand", [])]
        battlefield = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("battlefield", [])]
        graveyard = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("graveyard", [])]
        exile = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("exile", [])]
        commander = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("commander", [])]
        
        player_state = PlayerState(
            id=ps.id,
            user_id=ps.user_id,
            username=usernames.get(ps.user_id, "Unknown"),
            player_order=ps.player_order,
            is_active=ps.is_active,
            life_total=ps.life_total,
            poison_counters=ps.poison_counters,
            library=library,
            hand=hand,
            battlefield=battlefield,
            graveyard=graveyard,
            exile=exile,
            commander=commander,
        )
        players.append(player_state)
    
    active_username = usernames.get(db_game_state.active_player_id, "Unknown")
    
    game_state_data = GameStateData(
        id=db_game_state.id,
        game_room_id=db_game_state.game_room_id,
        current_turn=db_game_state.current_turn,
        active_player_id=db_game_state.active_player_id,
        active_player_username=active_username,
        current_phase=TurnPhase(db_game_state.current_phase),
        starting_player_id=db_game_state.starting_player_id,
        players=players,
        created_at=db_game_state.created_at,
    )
    
    return GameEngine(game_state_data)


def sync_engine_to_db(engine: GameEngine, db_session) -> None:
    from app.models.game_state import GameCard
    
    for player in engine.game_state.players:
        for zone_name in ["library", "hand", "battlefield", "graveyard", "exile", "commander"]:
            zone_cards = getattr(player, zone_name)
            for card in zone_cards:
                db_card = db_session.query(GameCard).filter(GameCard.id == card.id).first()
                if db_card:
                    db_card.zone = card.zone.value if hasattr(card.zone, 'value') else card.zone
                    db_card.position = card.position
                    db_card.is_tapped = card.is_tapped
                    db_card.is_face_up = card.is_face_up
                    db_card.battlefield_x = card.battlefield_x
                    db_card.battlefield_y = card.battlefield_y
                    db_card.is_attacking = card.is_attacking
                    db_card.is_blocking = card.is_blocking
                    db_card.damage_received = card.damage_received
    
    db_session.commit()
