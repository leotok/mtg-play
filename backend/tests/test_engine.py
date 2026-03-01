"""Tests for the game engine."""
import pytest
from datetime import datetime
from app.engine.game_engine import GameEngine
from app.engine.models import (
    GameStateData,
    PlayerState,
    Card,
    CardZone,
    TurnPhase,
    ManaColor,
    MoveCardInput,
)


def create_test_card(
    card_id: int,
    card_name: str,
    zone: CardZone,
    player_id: int,
    power: str = None,
    toughness: str = None,
    position: int = 0,
) -> Card:
    return Card(
        id=card_id,
        card_scryfall_id=f"test-{card_id}",
        card_name=card_name,
        mana_cost=None,
        cmc=None,
        type_line=None,
        oracle_text=None,
        colors=None,
        power=power,
        toughness=toughness,
        keywords=None,
        image_uris=None,
        card_faces=None,
        zone=zone,
        position=position,
        is_tapped=False,
        is_face_up=True,
        battlefield_x=None,
        battlefield_y=None,
        is_attacking=False,
        is_blocking=False,
        is_summoning_sick=True,
        damage_received=0,
        player_id=player_id,
    )


def create_test_game_state() -> GameStateData:
    player1 = PlayerState(
        id=1,
        user_id=1,
        username="Player1",
        player_order=0,
        is_active=True,
        life_total=40,
        poison_counters=0,
        library=[create_test_card(1, "Card1", CardZone.LIBRARY, 1, position=i) for i in range(7)],
        hand=[create_test_card(10, "HandCard1", CardZone.HAND, 1)],
        battlefield=[create_test_card(20, "Creature1", CardZone.BATTLEFIELD, 1, power="2", toughness="2", position=0)],
        graveyard=[],
        exile=[],
        commander=[create_test_card(30, "Commander1", CardZone.COMMANDER, 1)],
    )
    
    player2 = PlayerState(
        id=2,
        user_id=2,
        username="Player2",
        player_order=1,
        is_active=False,
        life_total=40,
        poison_counters=0,
        library=[create_test_card(2, "Card2", CardZone.LIBRARY, 2, position=i) for i in range(7)],
        hand=[],
        battlefield=[create_test_card(21, "Creature2", CardZone.BATTLEFIELD, 2, power="3", toughness="3", position=0)],
        graveyard=[],
        exile=[],
        commander=[create_test_card(31, "Commander2", CardZone.COMMANDER, 2)],
    )
    
    return GameStateData(
        id=1,
        game_room_id=1,
        current_turn=1,
        active_player_id=1,
        active_player_username="Player1",
        current_phase=TurnPhase.MAIN1,
        starting_player_id=1,
        players=[player1, player2],
        created_at=datetime.now(),
    )


class TestGameEngineInit:
    """Test game engine initialization."""
    
    def test_engine_initialization(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        assert engine.game_state is not None
        assert engine.phase_manager is not None
        assert engine.card_manager is not None
        assert engine.life_manager is not None
        assert engine.mana_manager is not None


class TestDrawCards:
    """Test drawing cards from library."""
    
    def test_draw_single_card(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        initial_library_size = len(engine.game_state.players[0].library)
        initial_hand_size = len(engine.game_state.players[0].hand)
        
        result = engine.draw_cards(player_id=1, count=1)
        
        assert result.success
        assert len(engine.game_state.players[0].library) == initial_library_size - 1
        assert len(engine.game_state.players[0].hand) == initial_hand_size + 1
    
    def test_draw_multiple_cards(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        result = engine.draw_cards(player_id=1, count=3)
        
        assert result.success
        assert len(engine.game_state.players[0].hand) == 4
    
    def test_draw_from_empty_library(self):
        game_state = create_test_game_state()
        game_state.players[0].library = []
        engine = GameEngine(game_state)
        
        with pytest.raises(Exception):
            engine.draw_cards(player_id=1, count=1)


class TestPlayCard:
    """Test playing cards from hand to battlefield."""
    
    def test_play_creature_from_hand(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        hand_card_id = engine.game_state.players[0].hand[0].id
        initial_hand_size = len(engine.game_state.players[0].hand)
        initial_battlefield_size = len(engine.game_state.players[0].battlefield)
        
        result = engine.play_card(
            card_id=hand_card_id,
            target_zone=CardZone.BATTLEFIELD,
        )
        
        assert result.success
        assert len(engine.game_state.players[0].hand) == initial_hand_size - 1
        assert len(engine.game_state.players[0].battlefield) == initial_battlefield_size + 1
    
    def test_play_card_from_invalid_zone(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        library_card_id = engine.game_state.players[0].library[0].id
        
        with pytest.raises(Exception):
            engine.play_card(
                card_id=library_card_id,
                target_zone=CardZone.BATTLEFIELD,
            )


class TestMoveCard:
    """Test moving cards between zones."""
    
    def test_move_card_to_graveyard(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        battlefield_card = engine.game_state.players[0].battlefield[0]
        
        result = engine.move_card(
            card_id=battlefield_card.id,
            target_zone=CardZone.GRAVEYARD,
        )
        
        assert result.success
        assert battlefield_card.zone == CardZone.GRAVEYARD
    
    def test_move_card_untaps_when_leaving_battlefield(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        battlefield_card = engine.game_state.players[0].battlefield[0]
        battlefield_card.is_tapped = True
        
        result = engine.move_card(
            card_id=battlefield_card.id,
            target_zone=CardZone.HAND,
        )
        
        assert result.success
        assert not battlefield_card.is_tapped


class TestTapCard:
    """Test tapping and untapping cards."""
    
    def test_tap_card(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        battlefield_card = engine.game_state.players[0].battlefield[0]
        assert not battlefield_card.is_tapped
        
        result = engine.tap_card(battlefield_card.id)
        
        assert result.success
        assert battlefield_card.is_tapped
    
    def test_untap_card(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        battlefield_card = engine.game_state.players[0].battlefield[0]
        battlefield_card.is_tapped = True
        
        result = engine.tap_card(battlefield_card.id)
        
        assert result.success
        assert not battlefield_card.is_tapped


class TestUntapAll:
    """Test untapping all cards."""
    
    def test_untap_all_cards(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        player = engine.game_state.players[0]
        for card in player.battlefield:
            card.is_tapped = True
        
        result = engine.untap_all(player_id=1)
        
        assert result.success
        for card in player.battlefield:
            assert not card.is_tapped


class TestAdjustLife:
    """Test adjusting player life totals."""
    
    def test_gain_life(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        result = engine.adjust_life(player_id=1, amount=5)
        
        assert result.success
        assert engine.game_state.players[0].life_total == 45
    
    def test_lose_life(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        result = engine.adjust_life(player_id=1, amount=-10)
        
        assert result.success
        assert engine.game_state.players[0].life_total == 30
    
    def test_life_cannot_go_negative(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        result = engine.adjust_life(player_id=1, amount=-100)
        
        assert result.success
        assert engine.game_state.players[0].life_total == 0


class TestPassPriority:
    """Test passing priority and advancing phases."""
    
    def test_advance_phase(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.MAIN1
        engine = GameEngine(game_state)
        
        result = engine.pass_priority()
        
        assert result.success
        assert result.phase_changed
        assert game_state.current_phase == TurnPhase.COMBAT_START
    
    def test_turn_change_at_end_of_phase(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.CLEANUP
        engine = GameEngine(game_state)
        
        result = engine.pass_priority()
        
        assert result.success
        assert result.turn_changed
        assert game_state.current_phase == TurnPhase.UNTAP
        assert game_state.current_turn == 2
        assert game_state.active_player_id == 2


class TestPhaseManager:
    """Test phase management."""
    
    def test_combat_phase_detection(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        game_state.current_phase = TurnPhase.COMBAT_ATTACK
        assert engine.phase_manager.is_combat_phase()
        
        game_state.current_phase = TurnPhase.MAIN1
        assert not engine.phase_manager.is_combat_phase()
    
    def test_main_phase_detection(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        game_state.current_phase = TurnPhase.MAIN1
        assert engine.phase_manager.is_main_phase()
        
        game_state.current_phase = TurnPhase.MAIN2
        assert engine.phase_manager.is_main_phase()
        
        game_state.current_phase = TurnPhase.COMBAT_ATTACK
        assert not engine.phase_manager.is_main_phase()


class TestManaManager:
    """Test mana pool management."""
    
    def test_add_mana(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        result = engine.add_mana(player_id=1, color=ManaColor.RED, amount=3)
        
        assert result.success
        assert engine.game_state.players[0].mana_pool[ManaColor.RED] == 3
    
    def test_spend_mana(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        engine.add_mana(player_id=1, color=ManaColor.BLUE, amount=2)
        result = engine.spend_mana(player_id=1, blue=1)
        
        assert result.success
        assert engine.game_state.players[0].mana_pool[ManaColor.BLUE] == 1
    
    def test_spend_mana_insufficient(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        with pytest.raises(Exception):
            engine.spend_mana(player_id=1, blue=5)
    
    def test_clear_mana_pool(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        engine.add_mana(player_id=1, color=ManaColor.WHITE, amount=3)
        engine.add_mana(player_id=1, color=ManaColor.BLUE, amount=2)
        
        result = engine.clear_mana(player_id=1)
        
        assert result.success
        assert len(engine.game_state.players[0].mana_pool) == 0


class TestCombatManager:
    """Test combat mechanics."""
    
    def test_declare_attacker(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.COMBAT_ATTACK
        engine = GameEngine(game_state)
        
        creature = engine.game_state.players[0].battlefield[0]
        creature.is_summoning_sick = False
        
        result = engine.declare_attacker(card_id=creature.id, target_player_id=2)
        
        assert result.success
        assert creature.is_attacking
        assert creature.is_tapped
    
    def test_cannot_attack_summoning_sick(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.COMBAT_ATTACK
        engine = GameEngine(game_state)
        
        creature = engine.game_state.players[0].battlefield[0]
        creature.is_summoning_sick = True
        
        with pytest.raises(Exception):
            engine.declare_attacker(card_id=creature.id, target_player_id=2)
    
    def test_cannot_attack_tapped(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.COMBAT_ATTACK
        engine = GameEngine(game_state)
        
        creature = engine.game_state.players[0].battlefield[0]
        creature.is_tapped = True
        creature.is_summoning_sick = False
        
        with pytest.raises(Exception):
            engine.declare_attacker(card_id=creature.id, target_player_id=2)


class TestMoveMultipleCards:
    """Test moving multiple cards at once."""
    
    def test_move_cards_batch(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        player = engine.game_state.players[0]
        card1 = create_test_card(100, "Card100", CardZone.HAND, 1)
        card2 = create_test_card(101, "Card101", CardZone.HAND, 1)
        player.hand.extend([card1, card2])
        
        moves = [
            MoveCardInput(card_id=card1.id, target_zone=CardZone.BATTLEFIELD, position=0),
            MoveCardInput(card_id=card2.id, target_zone=CardZone.BATTLEFIELD, position=1),
        ]
        
        result = engine.move_cards(moves)
        
        assert result.success
        assert len(player.hand) == 1
        assert len(player.battlefield) == 3


class TestSummoningSickness:
    """Test summoning sickness rules."""
    
    def test_summoning_sickness_set_on_play(self):
        game_state = create_test_game_state()
        engine = GameEngine(game_state)
        
        hand_card = engine.game_state.players[0].hand[0]
        
        result = engine.play_card(
            card_id=hand_card.id,
            target_zone=CardZone.BATTLEFIELD,
        )
        
        assert result.success
        assert hand_card.is_summoning_sick
    
    def test_summoning_sickness_cleared_on_turn_start(self):
        game_state = create_test_game_state()
        game_state.current_phase = TurnPhase.CLEANUP
        game_state.players[0].is_active = True
        game_state.players[1].is_active = False
        engine = GameEngine(game_state)
        
        player1_creature = game_state.players[0].battlefield[0]
        player1_creature.is_summoning_sick = True
        
        player2_creature = game_state.players[1].battlefield[0]
        player2_creature.is_summoning_sick = True
        
        result = engine.pass_priority()
        
        assert result.turn_changed
        assert player1_creature.is_summoning_sick
        assert not player2_creature.is_summoning_sick
