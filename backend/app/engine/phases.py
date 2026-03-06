from typing import Optional
from app.engine.models import TurnPhase, GameStateData, PlayerState, ActionResult
from app.engine.exceptions import InvalidPhaseError, InvalidPlayerError


PHASE_ORDER = [
    TurnPhase.UNTAP,
    TurnPhase.UPKEEP,
    TurnPhase.DRAW,
    TurnPhase.MAIN1,
    TurnPhase.COMBAT_START,
    TurnPhase.COMBAT_ATTACK,
    TurnPhase.COMBAT_BLOCK,
    TurnPhase.COMBAT_DAMAGE,
    TurnPhase.COMBAT_END,
    TurnPhase.MAIN2,
    TurnPhase.END,
    TurnPhase.CLEANUP,
]


class PhaseManager:
    def __init__(self, game_state: GameStateData):
        self.game_state = game_state
    
    def get_current_phase(self) -> TurnPhase:
        return self.game_state.current_phase
    
    def get_current_player(self) -> PlayerState:
        for player in self.game_state.players:
            if player.user_id == self.game_state.active_player_id:
                return player
        raise InvalidPlayerError("Active player not found")
    
    def get_player_by_id(self, user_id: int) -> PlayerState:
        for player in self.game_state.players:
            if player.user_id == user_id:
                return player
        raise InvalidPlayerError(f"Player {user_id} not found in game")
    
    def get_player_state_by_id(self, player_state_id: int) -> PlayerState:
        for player in self.game_state.players:
            if player.id == player_state_id:
                return player
        raise InvalidPlayerError(f"Player state {player_state_id} not found")
    
    def validate_active_player(self, user_id: int) -> None:
        if user_id != self.game_state.active_player_id:
            raise InvalidPlayerError("Only the active player can perform this action")
    
    def is_combat_phase(self) -> bool:
        return self.game_state.current_phase in [
            TurnPhase.COMBAT_START,
            TurnPhase.COMBAT_ATTACK,
            TurnPhase.COMBAT_BLOCK,
            TurnPhase.COMBAT_DAMAGE,
            TurnPhase.COMBAT_END,
        ]
    
    def is_main_phase(self) -> bool:
        return self.game_state.current_phase in [TurnPhase.MAIN1, TurnPhase.MAIN2]
    
    def can_cast_spells(self) -> bool:
        return self.is_main_phase() or self.game_state.current_phase == TurnPhase.UPKEEP
    
    def can_play_land(self) -> bool:
        """Lands can only be played during Main1 or Main2."""
        return self.is_main_phase()
    
    def can_attack(self) -> bool:
        return self.game_state.current_phase == TurnPhase.COMBAT_ATTACK
    
    def can_block(self) -> bool:
        return self.game_state.current_phase == TurnPhase.COMBAT_BLOCK
    
    def advance_phase(self) -> tuple[TurnPhase, TurnPhase, bool, int]:
        current_phase = self.game_state.current_phase
        current_index = PHASE_ORDER.index(current_phase)
        
        if current_index < len(PHASE_ORDER) - 1:
            next_phase = PHASE_ORDER[current_index + 1]
            self.game_state.current_phase = next_phase
            return current_phase, next_phase, False, self.game_state.active_player_id
        else:
            return self._start_next_turn()
    
    def _start_next_turn(self) -> tuple[TurnPhase, TurnPhase, bool, int]:
        player_states = sorted(self.game_state.players, key=lambda p: p.player_order)
        
        current_player = self.get_current_player()
        current_order = current_player.player_order
        next_order = (current_order + 1) % len(player_states)
        next_player = player_states[next_order]
        
        for player in self.game_state.players:
            player.is_active = (player.user_id == next_player.user_id)
            player.lands_played_this_turn = 0
        
        self.game_state.active_player_id = next_player.user_id
        self.game_state.active_player_username = next_player.username
        self.game_state.current_turn += 1
        self.game_state.current_phase = TurnPhase.UNTAP
        
        return TurnPhase.CLEANUP, TurnPhase.UNTAP, True, next_player.user_id
    
    def set_phase(self, phase: TurnPhase) -> None:
        if phase not in PHASE_ORDER:
            raise InvalidPhaseError(f"Invalid phase: {phase}")
        self.game_state.current_phase = phase
    
    def set_turn(self, player_id: int) -> None:
        player = self.get_player_by_id(player_id)
        self.game_state.active_player_id = player_id
        self.game_state.active_player_username = player.username
        self.game_state.current_phase = TurnPhase.UNTAP
        self.game_state.current_turn += 1
        
        for p in self.game_state.players:
            p.is_active = (p.user_id == player_id)


def create_action_result(
    game_state: GameStateData,
    phase_changed: bool = False,
    turn_changed: bool = False,
    message: str | None = None,
    affected_cards: list[int] | None = None,
) -> ActionResult:
    return ActionResult(
        success=True,
        message=message,
        game_state=game_state,
        phase_changed=phase_changed,
        turn_changed=turn_changed,
        new_phase=game_state.current_phase if phase_changed else None,
        new_turn=game_state.current_turn if turn_changed else None,
        new_active_player=game_state.active_player_id if turn_changed else None,
        affected_cards=affected_cards or [],
    )
