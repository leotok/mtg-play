from typing import Optional, Set, TYPE_CHECKING
from app.engine.models import (
    GameStateData,
    PlayerState,
    CardZone,
    TurnPhase,
    MoveCardInput,
    ManaColor,
    ActionResult,
    card_to_engine,
    parse_mana_cost,
    get_mana_cost_for_card,
    get_card_face_mana_cost,
    card_needs_side_selection,
    get_card_sides_info,
)
from app.engine.exceptions import (
    InvalidCardError,
    InvalidPlayerError,
    InvalidZoneError,
    EmptyLibraryError,
    TooManyLandsError,
    InvalidPhaseForLandError,
    InvalidPhaseError,
    InsufficientResourcesError,
)
from app.engine.phases import PhaseManager, create_action_result
from app.engine.actions import CardManager, LifeManager, ManaManager, CombatManager, LandTapper
from app.engine.land_utils import get_land_colors as _get_land_colors

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
        side_index: Optional[int] = None,
    ) -> ActionResult:
        card = self.card_manager.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        if card.zone not in [CardZone.HAND.value, CardZone.COMMANDER.value]:
            raise InvalidZoneError("Card must be in hand or commander zone to play")
        
        player = self.phase_manager.get_player_by_id(card.player_id)
        
        is_land = card.type_line and "land" in card.type_line.lower()
        
        if is_land:
            if not self.phase_manager.can_play_land(card.player_id):
                raise InvalidPhaseForLandError("Lands can only be played during main phase")
            if player.lands_played_this_turn >= 1:
                raise TooManyLandsError("You may only play 1 land per turn")
            player.lands_played_this_turn += 1
        else:
            if not self.phase_manager.can_cast_spells(card.player_id):
                raise InvalidPhaseError("Can only cast spells during your main phase")
        
        if side_index is not None:
            card.played_as_side = side_index
        
        needed_mana, hybrid_options = get_mana_cost_for_card(card)
        
        if needed_mana or hybrid_options:
            land_tapper = LandTapper(player)
            
            if not self._can_afford_mana(needed_mana, hybrid_options, player, land_tapper):
                raise InsufficientResourcesError("Not enough mana to play this card")
            
            pool = player.mana_pool
            GENERIC_KEY = "generic"
            
            # Handle generic mana - can be paid with any color from pool or lands
            generic_needed = needed_mana.pop(GENERIC_KEY, 0)
            
            # Pay colored from pool (skip generic and colorless)
            for color, amount in list(needed_mana.items()):
                if color == ManaColor.COLORLESS:
                    continue
                pool_amount = pool.get(color, 0)
                if pool_amount >= amount:
                    pool[color] = pool_amount - amount
                    needed_mana[color] = 0
                else:
                    needed_mana[color] = amount - pool_amount
                    pool[color] = 0
            
            # For remaining colored mana, tap lands
            remaining_colored = {k: v for k, v in needed_mana.items() if v > 0 and k != ManaColor.COLORLESS}
            
            tapped_lands = []
            for hybrid_choice in hybrid_options:
                colors_in_hybrid = list(hybrid_choice)
                paid_from_pool = False
                
                for color in colors_in_hybrid:
                    if pool.get(color, 0) > 0:
                        pool[color] = pool.get(color, 0) - 1
                        paid_from_pool = True
                        break
                
                if not paid_from_pool:
                    try:
                        result = land_tapper.tap_lands_for_mana({colors_in_hybrid[0]: 1})
                        tapped_lands.extend([k for k, v in result.items() if v > 0])
                    except:
                        pass
            
            # Tap remaining colored lands
            if remaining_colored:
                try:
                    land_tapper.tap_lands_for_mana(remaining_colored)
                except:
                    pass
            
            # Tap lands for generic - can use any land
            if generic_needed > 0:
                try:
                    land_tapper.tap_lands_for_generic(generic_needed)
                except:
                    pass
        
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
        
        if not card.is_tapped and card.type_line and "land" in card.type_line.lower():
            player = self.phase_manager.get_player_by_id(card.player_id)
            
            colors_produced = _get_land_colors(card.type_line, card.card_name, card.oracle_text)
            
            if len(colors_produced) > 1:
                for color in colors_produced:
                    if player.mana_pool.get(color, 0) > 0:
                        player.mana_pool[color] -= 1
            elif colors_produced:
                color = next(iter(colors_produced))
                if player.mana_pool.get(color, 0) > 0:
                    player.mana_pool[color] -= 1
            else:
                for color in [ManaColor.WHITE, ManaColor.BLUE, ManaColor.BLACK, ManaColor.RED, ManaColor.GREEN]:
                    if player.mana_pool.get(color, 0) > 0:
                        player.mana_pool[color] -= 1
                        break
                else:
                    if player.mana_pool.get(ManaColor.COLORLESS, 0) > 0:
                        player.mana_pool[ManaColor.COLORLESS] -= 1
        
        action = "untapped" if not card.is_tapped else "tapped"
        
        return create_action_result(
            self.game_state,
            affected_cards=[card_id],
            message=f"{card.card_name} {action}",
        )
    
    def get_card_colors(self, card_id: int) -> Set[ManaColor]:
        """Get the colors a card can produce (for lands).
        
        Args:
            card_id: The ID of the card to check.
            
        Returns:
            Set of ManaColor values the land can produce.
        """
        card = self.card_manager.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        if not card.type_line or "land" not in card.type_line.lower():
            return set()
        
        return _get_land_colors(card.type_line, card.card_name, card.oracle_text)
    
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
        current_phase, next_phase, turn_changed, new_active_player = self.phase_manager.advance_phase()
        
        if current_phase == TurnPhase.DRAW:
            self.draw_cards(player_id=new_active_player, count=1)
        
        for player in self.game_state.players:
            player.mana_pool.clear()
        
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
    
    def get_valid_plays(self, player_id: int) -> dict:
        """Get all valid plays for a player based on current game state.
        
        Args:
            player_id: The ID of the player to get valid plays for
            
        Returns:
            Dictionary with:
                - current_phase: TurnPhase
                - can_cast_spells: bool
                - can_play_land: bool
                - available_mana: dict of ManaColor -> int
                - untapped_lands_count: int
                - plays: list of dicts with card info and playability
        """
        from app.engine.models import Card
        
        player = self.phase_manager.get_player_by_id(player_id)
        current_phase = self.game_state.current_phase
        can_cast = self.phase_manager.can_cast_spells(player_id)
        can_play_land = self.phase_manager.can_play_land(player_id) and player.lands_played_this_turn < 1
        
        available_mana = dict(player.mana_pool)
        
        land_tapper = LandTapper(player)
        untapped_lands = land_tapper.get_untapped_lands()
        untapped_lands_count = len(untapped_lands)
        
        playable_cards = []
        
        if can_cast or can_play_land:
            all_cards = player.hand + player.commander
            
            for card in all_cards:
                source_zone = CardZone.HAND if card in player.hand else CardZone.COMMANDER
                
                is_land = card.type_line and "land" in card.type_line.lower()
                
                if is_land:
                    can_afford = can_play_land and self._can_afford_mana({}, [], player, land_tapper)
                else:
                    can_afford = can_cast
                    if can_cast:
                        needs_side_selection = card_needs_side_selection(card)
                        
                        if needs_side_selection:
                            sides_info = get_card_sides_info(card)
                            
                            affordable_sides = []
                            for side in sides_info:
                                regular_mana, hybrid_options = parse_mana_cost(side.get('mana_cost'))
                                if self._can_afford_mana(regular_mana, hybrid_options, player, land_tapper):
                                    affordable_sides.append(side)
                            
                            can_afford = len(affordable_sides) > 0
                        else:
                            regular_mana, hybrid_options = get_mana_cost_for_card(card)
                            can_afford = self._can_afford_mana(regular_mana, hybrid_options, player, land_tapper)
                
                playable_cards.append({
                    'card_id': card.id,
                    'card_name': card.card_name,
                    'zone': source_zone.value,
                    'mana_cost': card.mana_cost if not is_land else None,
                    'can_afford_mana': can_afford,
                    'needs_side_selection': False,
                    'sides': None,
                })
        
        return {
            'current_phase': current_phase,
            'can_cast_spells': can_cast,
            'can_play_land': can_play_land,
            'available_mana': {k.value: v for k, v in available_mana.items()},
            'untapped_lands_count': untapped_lands_count,
            'plays': playable_cards,
        }
    
    def _can_afford_mana(self, needed_mana: dict, hybrid_options: list, player: PlayerState, land_tapper: LandTapper) -> bool:
        """Check if player can afford the mana cost.
        
        Args:
            needed_mana: Dictionary of ManaColor -> amount needed
            hybrid_options: List of sets representing hybrid/payment alternatives
            player: The player whose mana to check
            land_tapper: LandTapper instance for checking land production
            
        Returns:
            True if can afford, False otherwise
        """
        if not needed_mana and not hybrid_options:
            return True
        
        pool = player.mana_pool
        GENERIC_KEY = "generic"
        
        if not hybrid_options:
            remaining = dict(needed_mana)
            
            # Handle generic mana first
            generic_needed = remaining.pop(GENERIC_KEY, 0)
            
            # Pay colored from pool
            for color, amount in list(remaining.items()):
                pool_amount = pool.get(color, 0)
                if pool_amount >= amount:
                    remaining[color] = 0
                else:
                    remaining[color] = amount - pool_amount
            
            remaining_colored = sum(v for v in remaining.values() if v > 0)
            
            # Check if we can afford
            total_pool = sum(pool.values())
            
            if generic_needed > 0:
                # Check if pool has the SPECIFIC colored mana needed
                can_pay_colored_from_pool = True
                for color, amount in remaining.items():
                    if amount > 0:
                        if pool.get(color, 0) < amount:
                            can_pay_colored_from_pool = False
                            break
                
                if can_pay_colored_from_pool:
                    # Pool has all colored needed, check generic
                    pool_after_colored = total_pool - remaining_colored
                    if pool_after_colored >= generic_needed:
                        return True
                    # Can use lands for remaining generic
                    if land_tapper.can_produce_generic(generic_needed - pool_after_colored):
                        return True
                else:
                    # Pool doesn't have all specific colors - need to use lands for colored
                    if remaining_colored > 0:
                        if land_tapper.can_produce_mana(remaining):
                            # Check generic
                            if total_pool >= generic_needed:
                                return True
                            if land_tapper.can_produce_generic(generic_needed):
                                return True
            elif remaining_colored > 0:
                return land_tapper.can_produce_mana(remaining)
            
            return False
        
        for hybrid_choice in hybrid_options:
            remaining = dict(needed_mana)
            generic_needed = remaining.pop(GENERIC_KEY, 0)
            phyrexian_count = sum(1 for opts in hybrid_options if len(opts) == 1)
            life_payment = phyrexian_count * 2
            
            # For hybrid, need to check if we can pay each hybrid
            hybrid_needed = len(hybrid_options)
            
            # Count how many hybrid can be paid from pool
            hybrid_from_pool = 0
            for color in hybrid_choice:
                hybrid_from_pool += min(pool.get(color, 0), hybrid_needed)
            
            hybrid_still_needed = max(0, hybrid_needed - hybrid_from_pool)
            
            # For hybrid: need colored lands for each hybrid still needed
            # For generic: can use any remaining land
            # Total lands needed = hybrid_still_needed + generic_needed
            total_lands_needed = hybrid_still_needed + generic_needed
            
            if total_lands_needed == 0:
                return True
            
            # Check if pool can cover everything
            total_pool = sum(pool.values())
            if total_pool >= total_lands_needed:
                return True
            
            # Need to use lands
            untapped_count = len(land_tapper.get_untapped_lands())
            
            # Check if we can produce enough mana from lands
            if untapped_count >= total_lands_needed:
                # But we also need to verify we can produce the SPECIFIC colors for hybrid
                if hybrid_still_needed > 0:
                    # Check if we can produce hybrid colors from lands
                    if land_tapper.can_produce_mana({c: 1 for c in hybrid_choice}, require_all=False):
                        # After using lands for hybrid, can we still get generic?
                        remaining_lands = untapped_count - hybrid_still_needed
                        if remaining_lands >= generic_needed:
                            return True
                else:
                    # Only generic needed
                    if land_tapper.can_produce_generic(generic_needed):
                        return True
            
            if life_payment > 0 and player.life_total >= life_payment:
                return True
        
        return False
    
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
    from app.engine.models import ManaColor
    
    players = []
    
    for ps in db_player_states:
        player_id = ps.user_id
        
        library = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("library", [])]
        hand = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("hand", [])]
        battlefield = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("battlefield", [])]
        graveyard = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("graveyard", [])]
        exile = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("exile", [])]
        commander = [card_to_engine(c, player_id) for c in db_cards_by_player.get(player_id, {}).get("commander", [])]
        
        mana_pool = {
            ManaColor.WHITE: ps.white_mana or 0,
            ManaColor.BLUE: ps.blue_mana or 0,
            ManaColor.BLACK: ps.black_mana or 0,
            ManaColor.RED: ps.red_mana or 0,
            ManaColor.GREEN: ps.green_mana or 0,
            ManaColor.COLORLESS: ps.colorless_mana or 0,
        }
        
        player_state = PlayerState(
            id=ps.id,
            user_id=ps.user_id,
            username=usernames.get(ps.user_id, "Unknown"),
            player_order=ps.player_order,
            is_active=ps.is_active,
            life_total=ps.life_total,
            poison_counters=ps.poison_counters,
            mana_pool=mana_pool,
            lands_played_this_turn=ps.lands_played_this_turn or 0,
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
    from app.models.game_state import GameCard, PlayerGameState, GameState as DBGameState
    from app.engine.models import ManaColor
    
    db_game_state = db_session.query(DBGameState).filter(
        DBGameState.id == engine.game_state.id
    ).first()
    if db_game_state:
        db_game_state.current_phase = engine.game_state.current_phase.value
        db_game_state.current_turn = engine.game_state.current_turn
        db_game_state.active_player_id = engine.game_state.active_player_id
    
    for player in engine.game_state.players:
        db_player = db_session.query(PlayerGameState).filter(
            PlayerGameState.user_id == player.user_id,
            PlayerGameState.game_state_id == engine.game_state.id
        ).first()
        
        if db_player:
            db_player.white_mana = player.mana_pool.get(ManaColor.WHITE, 0)
            db_player.blue_mana = player.mana_pool.get(ManaColor.BLUE, 0)
            db_player.black_mana = player.mana_pool.get(ManaColor.BLACK, 0)
            db_player.red_mana = player.mana_pool.get(ManaColor.RED, 0)
            db_player.green_mana = player.mana_pool.get(ManaColor.GREEN, 0)
            db_player.colorless_mana = player.mana_pool.get(ManaColor.COLORLESS, 0)
            db_player.life_total = player.life_total
            db_player.is_active = player.is_active
            db_player.lands_played_this_turn = player.lands_played_this_turn
        
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
