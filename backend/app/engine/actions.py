from typing import Optional
from app.engine.models import (
    GameStateData,
    PlayerState,
    Card,
    CardZone,
    TurnPhase,
    ManaColor,
)
from app.engine.exceptions import (
    InvalidCardError,
    InvalidPlayerError,
    InvalidZoneError,
    EmptyLibraryError,
    InsufficientResourcesError,
    InvalidPhaseError,
)
from app.engine.phases import PhaseManager


class CardManager:
    def __init__(self, game_state: GameStateData, phase_manager: PhaseManager):
        self.game_state = game_state
        self.phase_manager = phase_manager
    
    def get_card(self, card_id: int) -> Card | None:
        for player in self.game_state.players:
            for zone_name in ["library", "hand", "battlefield", "graveyard", "exile", "commander"]:
                zone_cards = getattr(player, zone_name)
                for card in zone_cards:
                    if card.id == card_id:
                        return card
        return None
    
    def get_card_owner(self, card_id: int) -> PlayerState:
        card = self.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        return self.phase_manager.get_player_by_id(card.player_id)
    
    def validate_card_ownership(self, card_id: int, user_id: int) -> Card:
        card = self.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        if card.player_id != user_id:
            raise InvalidCardError(f"Card {card_id} does not belong to player {user_id}")
        return card
    
    def move_card(self, card: Card, target_zone: CardZone, position: int = 0) -> None:
        current_zone = CardZone(card.zone)
        
        player = self.phase_manager.get_player_by_id(card.player_id)
        
        current_zone_list = self._get_zone_list(player, current_zone)
        if card in current_zone_list:
            current_zone_list.remove(card)
        
        card.zone = target_zone
        card.position = position
        
        target_zone_list = self._get_zone_list(player, target_zone)
        target_zone_list.append(card)
        
        if current_zone == CardZone.BATTLEFIELD and target_zone != CardZone.BATTLEFIELD:
            card.is_tapped = False
            card.is_attacking = False
            card.is_blocking = False
    
    def _get_zone_list(self, player: PlayerState, zone: CardZone) -> list[Card]:
        zone_map = {
            CardZone.LIBRARY: player.library,
            CardZone.HAND: player.hand,
            CardZone.BATTLEFIELD: player.battlefield,
            CardZone.GRAVEYARD: player.graveyard,
            CardZone.EXILE: player.exile,
            CardZone.COMMANDER: player.commander,
        }
        return zone_map.get(zone, [])
    
    def draw_cards(self, player_id: int, count: int = 1) -> list[Card]:
        player = self.phase_manager.get_player_by_id(player_id)
        
        if not player.library:
            raise EmptyLibraryError(f"Player {player_id} has no cards in library")
        
        drawn = []
        for _ in range(count):
            if not player.library:
                break
            
            top_card = min(player.library, key=lambda c: c.position)
            player.library.remove(top_card)
            player.hand.append(top_card)
            drawn.append(top_card)
        
        return drawn
    
    def discard_card(self, player_id: int, card_id: int) -> Card:
        player = self.phase_manager.get_player_by_id(player_id)
        
        card = None
        for c in player.hand:
            if c.id == card_id:
                card = c
                break
        
        if not card:
            raise InvalidCardError(f"Card {card_id} not in hand")
        
        player.hand.remove(card)
        player.graveyard.append(card)
        card.zone = CardZone.GRAVEYARD
        
        return card
    
    def tap_card(self, card_id: int) -> Card:
        card = self.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        if card.zone != CardZone.BATTLEFIELD:
            raise InvalidZoneError("Can only tap cards on the battlefield")
        
        card.is_tapped = not card.is_tapped
        return card
    
    def untap_all(self, player_id: int) -> list[Card]:
        player = self.phase_manager.get_player_by_id(player_id)
        
        untapped = []
        for card in player.battlefield:
            if card.is_tapped:
                card.is_tapped = False
                untapped.append(card)
        
        return untapped
    
    def set_card_position(self, card_id: int, x: float, y: float) -> Card:
        card = self.get_card(card_id)
        if not card:
            raise InvalidCardError(f"Card {card_id} not found")
        
        if card.zone != CardZone.BATTLEFIELD:
            raise InvalidZoneError("Can only position cards on the battlefield")
        
        card.battlefield_x = x
        card.battlefield_y = y
        
        return card
    
    def sort_zone_by_position(self, player: PlayerState, zone: CardZone) -> None:
        zone_list = self._get_zone_list(player, zone)
        zone_list.sort(key=lambda c: c.position)


class LifeManager:
    def __init__(self, game_state: GameStateData, phase_manager: PhaseManager):
        self.game_state = game_state
        self.phase_manager = phase_manager
    
    def adjust_life(self, player_id: int, amount: int) -> tuple[PlayerState, int]:
        player = self.phase_manager.get_player_by_id(player_id)
        
        old_life = player.life_total
        player.life_total += amount
        
        if player.life_total < 0:
            player.life_total = 0
        
        return player, old_life
    
    def deal_damage(self, target_id: int, damage: int, source_id: Optional[int] = None) -> tuple[PlayerState | Card, int]:
        target_player = None
        target_card = None
        
        for player in self.game_state.players:
            if player.user_id == target_id:
                target_player = player
                break
        
        if not target_player:
            card = None
            for player in self.game_state.players:
                for c in player.battlefield:
                    if c.id == target_id:
                        card = c
                        break
            if card:
                target_card = card
        
        if not target_player and not target_card:
            raise InvalidPlayerError(f"Target {target_id} not found")
        
        if target_player:
            old_life = target_player.life_total
            target_player.life_total = max(0, target_player.life_total - damage)
            return target_player, old_life - target_player.life_total
        else:
            old_damage = target_card.damage_received
            target_card.damage_received += damage
            return target_card, target_card.damage_received - old_damage
    
    def add_poison(self, player_id: int, amount: int) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        player.poison_counters += amount
        return player
    
    def add_commander_damage(self, player_id: int, source_player_id: int, amount: int) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        
        if source_player_id not in player.commander_damage:
            player.commander_damage[source_player_id] = 0
        
        player.commander_damage[source_player_id] += amount
        
        return player


class ManaManager:
    def __init__(self, game_state: GameStateData, phase_manager: PhaseManager):
        self.game_state = game_state
        self.phase_manager = phase_manager
    
    def add_mana(self, player_id: int, color: ManaColor, amount: int = 1) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        
        if color not in player.mana_pool:
            player.mana_pool[color] = 0
        
        player.mana_pool[color] += amount
        
        return player
    
    def spend_mana(self, player_id: int, **costs: int) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        
        for color, amount in costs.items():
            if color not in player.mana_pool:
                player.mana_pool[color] = 0
            
            if player.mana_pool[color] < amount:
                raise InsufficientResourcesError(
                    f"Insufficient {color} mana. Have {player.mana_pool[color]}, need {amount}"
                )
        
        for color, amount in costs.items():
            player.mana_pool[color] -= amount
        
        return player
    
    def get_mana_pool(self, player_id: int) -> dict[ManaColor, int]:
        player = self.phase_manager.get_player_by_id(player_id)
        return player.mana_pool.copy()
    
    def clear_mana_pool(self, player_id: int) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        player.mana_pool.clear()
        return player
    
    def adjust_mana(self, player_id: int, **kwargs: int) -> PlayerState:
        player = self.phase_manager.get_player_by_id(player_id)
        
        for color_str, amount in kwargs.items():
            try:
                color = ManaColor(color_str)
            except ValueError:
                color = ManaColor.COLORLESS
            
            if color not in player.mana_pool:
                player.mana_pool[color] = 0
            
            player.mana_pool[color] += amount
        
        return player


class CombatManager:
    def __init__(self, game_state: GameStateData, phase_manager: PhaseManager):
        self.game_state = game_state
        self.phase_manager = phase_manager
    
    def declare_attacker(self, card_id: int, target_player_id: Optional[int] = None) -> Card:
        card = None
        for player in self.game_state.players:
            for c in player.battlefield:
                if c.id == card_id:
                    card = c
                    break
        
        if not card:
            raise InvalidCardError(f"Card {card_id} not found on battlefield")
        
        if self.phase_manager.game_state.current_phase != TurnPhase.COMBAT_ATTACK:
            raise InvalidPhaseError("Can only declare attackers during combat attack phase")
        
        if card.is_summoning_sick:
            raise InvalidCardError(f"{card.card_name} is summoning sick and cannot attack")
        
        if card.is_tapped:
            raise InvalidCardError(f"{card.card_name} is tapped and cannot attack")
        
        card.is_attacking = True
        card.is_tapped = True
        
        return card
    
    def declare_blocker(self, attacker_id: int, blocker_id: int) -> tuple[Card, Card]:
        attacker = None
        blocker = None
        
        for player in self.game_state.players:
            for c in player.battlefield:
                if c.id == attacker_id:
                    attacker = c
                if c.id == blocker_id:
                    blocker = c
        
        if not attacker:
            raise InvalidCardError(f"Attacker {attacker_id} not found")
        
        if not blocker:
            raise InvalidCardError(f"Blocker {blocker_id} not found")
        
        if not attacker.is_attacking:
            raise InvalidCardError(f"Card {attacker_id} is not attacking")
        
        if self.phase_manager.game_state.current_phase != TurnPhase.COMBAT_BLOCK:
            raise InvalidPhaseError("Can only declare blockers during combat block phase")
        
        if blocker.is_tapped:
            raise InvalidCardError(f"{blocker.card_name} is tapped and cannot block")
        
        if blocker.is_summoning_sick:
            raise InvalidCardError(f"{blocker.card_name} is summoning sick and cannot block")
        
        blocker.is_blocking = True
        blocker.is_tapped = True
        
        return attacker, blocker
    
    def resolve_combat_damage(self) -> list[tuple[Card, Card, int]]:
        damage_events = []
        
        attackers = []
        blockers = []
        
        for player in self.game_state.players:
            for card in player.battlefield:
                if card.is_attacking:
                    attackers.append(card)
                if card.is_blocking:
                    blockers.append(card)
        
        for attacker in attackers:
            blocking_cards = [c for c in blockers if c.is_blocking and getattr(c, 'blocked_by', None) == attacker.id]
            
            if not blocking_cards:
                if attacker.is_attacking and attacker.id in [a.id for a in attackers]:
                    for player in self.game_state.players:
                        if player.user_id == self.phase_manager.game_state.active_player_id:
                            continue
                        
                        damage_manager = LifeManager(self.game_state, self.phase_manager)
                        damage_manager.deal_damage(player.user_id, int(attacker.power) if attacker.power else 0)
            
            else:
                for blocker in blocking_cards:
                    attacker_power = int(attacker.power) if attacker.power else 0
                    blocker_power = int(blocker.power) if blocker.power else 0
                    
                    damage_events.append((attacker, blocker, attacker_power))
                    damage_events.append((blocker, attacker, blocker_power))
        
        return damage_events
    
    def clear_combat(self) -> None:
        for player in self.game_state.players:
            for card in player.battlefield:
                card.is_attacking = False
                card.is_blocking = False
    
    def destroy_dead_creatures(self) -> list[Card]:
        destroyed = []
        
        for player in self.game_state.players:
            surviving = []
            
            for card in player.battlefield:
                toughness = int(card.toughness) if card.toughness else None
                
                if toughness and card.damage_received >= toughness:
                    player.graveyard.append(card)
                    destroyed.append(card)
                else:
                    surviving.append(card)
            
            player.battlefield = surviving
        
        return destroyed


class LandTapper:
    """Handles auto-tapping lands to produce mana for spell casting."""
    
    LAND_TYPES = {
        "plains": ManaColor.WHITE,
        "island": ManaColor.BLUE,
        "swamp": ManaColor.BLACK,
        "mountain": ManaColor.RED,
        "forest": ManaColor.GREEN,
    }
    
    DUAL_LANDS_NOT_PAIN = [
        "tropical island", "badlands", "taiga", "scrubland", "volcanic island",
        "bayou", "savannah", "underground sea", "karplus sea", "fenland",
        "glowering", "rocky", "sequestered", "wildwood", "mistplain",
    ]
    
    TRIOMES = [
        "rau-triome", "jetmirs triome", "sidequarr triome", "zagoth triome", "ketria triome",
        "indy triome", "ulumari triome", "mosaic", "repentant", "cascade",
    ]
    
    SHOCK_LANDS = [
        "overgrown tomb", "watery grave", "blood crypt", "stomping ground", "temple garden",
        "hallowed fountain", "godless shrine", "iza", "breeding pool", "spire garden",
    ]
    
    PAIN_LANDS = [
        "karplus warmforest", "karplus nightfall", "shivan reef", "karam grul",
        "llanowar reborn", "vivien reed", "jordan", "dakmor salvage",
    ]
    
    def __init__(self, player: PlayerState):
        self.player = player
    
    def get_untapped_lands(self) -> list[Card]:
        """Get all untapped land cards from the player's battlefield."""
        return [
            card for card in self.player.battlefield
            if not card.is_tapped and self._is_land(card)
        ]
    
    def _is_land(self, card: Card) -> bool:
        """Check if a card is a land."""
        type_line = (card.type_line or "").lower()
        return "land" in type_line
    
    def _get_land_priority(self, card: Card) -> int:
        """Get priority for tapping a land (lower = tap first)."""
        type_line = (card.type_line or "").lower()
        name = (card.card_name or "").lower()
        
        if "basic" in type_line:
            return 1
        
        is_dual = any(dual in name for dual in self.DUAL_LANDS_NOT_PAIN)
        is_triome = "triome" in name
        is_shock = any(shock in name for shock in self.SHOCK_LANDS)
        is_pain = any(pain in name for pain in self.PAIN_LANDS)
        
        if is_dual:
            return 2
        if is_triome:
            return 3
        if is_shock:
            return 4
        if is_pain:
            return 5
        
        return 2
    
    def _get_land_colors(self, card: Card) -> set[ManaColor]:
        """Get the colors a land can produce based on its types."""
        type_line = (card.type_line or "").lower()
        name = (card.card_name or "").lower()
        
        colors = set()
        
        for land_type, color in self.LAND_TYPES.items():
            if land_type in type_line:
                colors.add(color)
        
        if any(dual in name for dual in self.DUAL_LANDS_NOT_PAIN):
            colors.add(ManaColor.COLORLESS)
        
        if "triome" in name:
            colors.update([ManaColor.GREEN, ManaColor.BLUE, ManaColor.RED])
        
        if any(shock in name for shock in self.SHOCK_LANDS):
            colors.add(ManaColor.COLORLESS)
        
        if any(pain in name for pain in self.PAIN_LANDS):
            colors.add(ManaColor.COLORLESS)
        
        if not colors:
            colors.add(ManaColor.COLORLESS)
        
        return colors
    
    def tap_lands_for_mana(self, needed: dict) -> dict:
        """Tap lands to produce the needed mana colors.
        
        Pays colored mana first, then generic/colorless mana.
        
        Args:
            needed: Dictionary of colors and amounts needed
            
        Returns:
            Dictionary of colors actually produced (may be more than needed)
            
        Raises:
            InsufficientResourcesError: If not enough lands can produce needed mana
        """
        needed = {k: v for k, v in needed.items() if v > 0}
        
        colored_mana = {k: v for k, v in needed.items() if k != ManaColor.COLORLESS}
        colorless_mana = needed.get(ManaColor.COLORLESS, 0)
        
        untapped = self.get_untapped_lands()
        untapped_sorted = sorted(untapped, key=self._get_land_priority)
        
        produced: dict = {}
        remaining = dict(colored_mana)
        
        for land in untapped_sorted:
            if not remaining:
                break
            
            land_colors = self._get_land_colors(land)
            
            for color in list(remaining.keys()):
                if remaining.get(color, 0) > 0 and color in land_colors:
                    land.is_tapped = True
                    
                    produced[color] = produced.get(color, 0) + 1
                    remaining[color] = remaining.get(color, 0) - 1
                    
                    if remaining[color] <= 0:
                        del remaining[color]
                    
                    break
        
        if remaining and sum(remaining.values()) > 0:
            missing = ", ".join([f"{color.value}: {amt}" for color, amt in remaining.items() if amt > 0])
            raise InsufficientResourcesError(
                f"Cannot produce required mana: {missing}. Not enough untapped lands."
            )
        
        if colorless_mana > 0:
            remaining_colorless = colorless_mana
            for land in untapped_sorted:
                if remaining_colorless <= 0:
                    break
                
                if not land.is_tapped:
                    land.is_tapped = True
                    produced[ManaColor.COLORLESS] = produced.get(ManaColor.COLORLESS, 0) + 1
                    remaining_colorless -= 1
            
            if remaining_colorless > 0:
                raise InsufficientResourcesError(
                    f"Cannot produce required mana: colorless: {remaining_colorless}. Not enough untapped lands."
                )
        
        return produced
