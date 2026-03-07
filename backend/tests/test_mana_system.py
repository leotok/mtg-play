"""
Comprehensive tests for the mana system.

Tests cover:
- Mana cost parsing (generic vs colorless)
- Land color detection
- Valid plays calculation (_can_afford_mana)
- Actual spell casting (play_card)
"""
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
    parse_mana_cost,
)
from app.engine.land_utils import get_land_colors
from app.engine.exceptions import InsufficientResourcesError


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_card(
    card_id: int,
    card_name: str,
    zone: CardZone,
    player_id: int,
    mana_cost: str = None,
    type_line: str = "Creature",
    oracle_text: str = None,
    power: str = "2",
    toughness: str = "2",
    position: int = 0,
    is_tapped: bool = False,
) -> Card:
    return Card(
        id=card_id,
        card_scryfall_id=f"test-{card_id}",
        card_name=card_name,
        mana_cost=mana_cost,
        cmc=None,
        type_line=type_line,
        oracle_text=oracle_text,
        colors=None,
        power=power,
        toughness=toughness,
        keywords=None,
        image_uris=None,
        card_faces=None,
        zone=zone,
        position=position,
        is_tapped=is_tapped,
        is_face_up=True,
        battlefield_x=None,
        battlefield_y=None,
        is_attacking=False,
        is_blocking=False,
        is_summoning_sick=True,
        damage_received=0,
        player_id=player_id,
    )


def create_land(
    card_id: int,
    card_name: str,
    player_id: int,
    type_line: str = "Basic Land",
    oracle_text: str = None,
    is_tapped: bool = False,
) -> Card:
    return create_card(
        card_id=card_id,
        card_name=card_name,
        zone=CardZone.BATTLEFIELD,
        player_id=player_id,
        mana_cost=None,
        type_line=type_line,
        oracle_text=oracle_text,
        power=None,
        toughness=None,
        is_tapped=is_tapped,
    )


def create_game_with_player(
    player_id: int,
    hand: list = None,
    battlefield: list = None,
    mana_pool: dict = None,
    is_active: bool = True,
    phase: TurnPhase = TurnPhase.MAIN1,
    commander: list = None,
) -> GameStateData:
    player = PlayerState(
        id=player_id,
        user_id=player_id,
        username=f"Player{player_id}",
        player_order=player_id - 1,
        is_active=is_active,
        life_total=40,
        poison_counters=0,
        library=[],
        hand=hand or [],
        battlefield=battlefield or [],
        graveyard=[],
        exile=[],
        commander=commander or [],
        mana_pool=mana_pool or {},
        lands_played_this_turn=0,
    )
    
    return GameStateData(
        id=1,
        game_room_id=1,
        current_turn=1,
        active_player_id=player_id if is_active else 2,
        active_player_username=f"Player{player_id}" if is_active else "Player2",
        current_phase=phase,
        starting_player_id=player_id,
        players=[player],
        created_at=datetime.now(),
    )


# =============================================================================
# TEST: MANA COST PARSING
# =============================================================================

class TestParseManaCost:
    """Tests for mana cost parsing."""
    
    def test_generic_number_parsed_as_generic(self):
        """Numbers in mana cost should be parsed as generic, not colorless."""
        result, _ = parse_mana_cost("{1}{R}")
        assert "generic" in result
        assert result["generic"] == 1
        assert ManaColor.RED in result
    
    def test_multiple_generic_numbers(self):
        """Multiple numbers should sum to generic."""
        result, _ = parse_mana_cost("{3}{R}{R}")
        assert result["generic"] == 3
        assert result[ManaColor.RED] == 2
    
    def test_explicit_colorless_C(self):
        """Explicit {C} should be COLORLESS, not generic."""
        result, _ = parse_mana_cost("{C}")
        assert ManaColor.COLORLESS in result
        assert result[ManaColor.COLORLESS] == 1
        assert "generic" not in result
    
    def test_mixed_white_and_generic(self):
        """White + numbers should parse correctly."""
        result, _ = parse_mana_cost("{W}{W}{3}")
        assert result[ManaColor.WHITE] == 2
        assert result["generic"] == 3
    
    def test_hybrid_with_generic(self):
        """Hybrid with number should include generic."""
        result, hybrid = parse_mana_cost("{2}{B/R}")
        assert result.get("generic", 0) == 2
        assert "black" in hybrid[0]
        assert "red" in hybrid[0]
        assert len(hybrid) == 1
    
    def test_hybrid_only(self):
        """Pure hybrid should have no generic."""
        result, hybrid = parse_mana_cost("{B/R}")
        assert len(result) == 0
        assert len(hybrid) == 1
    
    def test_empty_cost(self):
        """Empty cost should return empty dict."""
        result, hybrid = parse_mana_cost(None)
        assert result == {}
        assert hybrid == []


# =============================================================================
# TEST: LAND COLOR DETECTION
# =============================================================================

class TestLandColorDetection:
    """Tests for land color detection."""
    
    def test_basic_mountain_produces_red(self):
        """Basic Mountain should produce RED."""
        colors = get_land_colors("Basic Land — Mountain", "Mountain", None)
        assert ManaColor.RED in colors
        assert len(colors) == 1
    
    def test_basic_plains_produces_white(self):
        """Basic Plains should produce WHITE."""
        colors = get_land_colors("Basic Land — Plains", "Plains", None)
        assert ManaColor.WHITE in colors
    
    def test_eiganjo_produces_white(self):
        """Eiganjo with {T}: Add {W} should produce WHITE."""
        colors = get_land_colors(
            "Legendary Land",
            "Eiganjo, Seat of the Empire",
            "{T}: Add {W}."
        )
        assert ManaColor.WHITE in colors
    
    def test_blood_crypt_produces_black_and_red(self):
        """Blood Crypt should produce BLACK and RED."""
        colors = get_land_colors(
            "Land — Swamp Mountain",
            "Blood Crypt",
            "({T}: Add {B} or {R}.)"
        )
        assert ManaColor.BLACK in colors
        assert ManaColor.RED in colors
    
    def test_triome_produces_all_three_colors_from_oracle_text(self):
        """Triome should produce all 3 colors from oracle_text, NOT colorless (unless oracle_text says so)."""
        colors = get_land_colors(
            "Land",
            "Ketria Triome",
            "{T}: Add {W}, {U}, or {R}."
        )
        # Oracle text has W, U, R - should return all three colors
        assert ManaColor.WHITE in colors
        assert ManaColor.BLUE in colors
        assert ManaColor.RED in colors
        # Oracle text does NOT include {C}, so colorless should NOT be in the result
        assert ManaColor.COLORLESS not in colors
    
    def test_triome_does_not_produce_colorless_when_oracle_text_has_no_c(self):
        """Triome with oracle_text that only has colored mana should NOT produce colorless."""
        colors = get_land_colors(
            "Land",
            "Rau Triome",
            "({T}: Add {W}, {U}, or {R}.)"
        )
        # Oracle text has W, U, R - should return those colors
        assert ManaColor.WHITE in colors
        assert ManaColor.BLUE in colors
        assert ManaColor.RED in colors
        # Oracle text does NOT include {C}, so colorless should NOT be in the result
        assert ManaColor.COLORLESS not in colors
    
    def test_wastes_produces_colorless(self):
        """Wastes should produce colorless since oracle_text says {C}."""
        colors = get_land_colors(
            "Basic Land — Wastes",
            "Wastes",
            "{T}: Add {C}."
        )
        assert ManaColor.COLORLESS in colors
    
    def test_oracle_text_with_multiple_colors(self):
        """Land with oracle_text specifying multiple colors should return all of them."""
        colors = get_land_colors(
            "Land",
            "Blood Crypt",
            "({T}: Add {B} or {R}.)"
        )
        assert ManaColor.BLACK in colors
        assert ManaColor.RED in colors
    
    def test_generic_land_produces_colorless(self):
        """Land without basic type and no oracle_text should produce COLORLESS."""
        colors = get_land_colors("Land", "Some Land", None)
        assert ManaColor.COLORLESS in colors
    
    def test_basic_forest_produces_green(self):
        """Basic Forest should produce GREEN."""
        colors = get_land_colors("Basic Land — Forest", "Forest", None)
        assert ManaColor.GREEN in colors


# =============================================================================
# TEST: VALID PLAYS (_can_afford_mana)
# =============================================================================

class TestValidPlays:
    """Tests for valid plays calculation."""
    
    def test_generic_paid_with_any_land(self):
        """
        Scenario: Spell costs {1}{R}, player has 3 untapped lands (no red in pool)
        Expected: CAN play - generic can use any land, red from R/B land
        """
        # Spell: {1}{R} (1 generic + 1 red)
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{1}{R}")
        
        # Lands: 1 Mountain (R) + 2 R/B dual lands
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        dual1 = create_land(21, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        dual2 = create_land(22, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        
        game = create_game_with_player(
            1, hand=[spell], battlefield=[mountain, dual1, dual2]
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        # Find our spell
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == True
    
    def test_generic_only_with_untapped_lands(self):
        """
        Scenario: Spell costs {3}, player has 3 untapped lands
        Expected: CAN play - generic can use any 3 lands
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{3}")
        
        lands = [create_land(20 + i, f"Land{i}", 1, "Basic Land") for i in range(3)]
        
        game = create_game_with_player(1, hand=[spell], battlefield=lands)
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == True
    
    def test_not_enough_red_sources(self):
        """
        Scenario: Spell costs {R}{R}, player has 1 Mountain
        Expected: CANNOT play - only 1 red source, need 2
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{R}{R}")
        
        # Only 1 Mountain - can produce only 1 red
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        
        game = create_game_with_player(1, hand=[spell], battlefield=[mountain])
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_cannot_pay_blue_with_red_lands(self):
        """
        Scenario: Spell costs {1}{U}, player has 1 Mountain + 2 B/R dual lands
        Expected: CANNOT play - no blue source, can only produce red/black from lands
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{1}{U}")
        
        # Mountain produces RED
        # B/R lands produce BLACK or RED (no blue!)
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        dual1 = create_land(21, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        dual2 = create_land(22, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        
        game = create_game_with_player(1, hand=[spell], battlefield=[mountain, dual1, dual2])
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_not_enough_lands_for_generic_and_colored(self):
        """
        Scenario: Spell costs {4}{B}, player has 1 Mountain + 2 B/R dual lands (3 total)
        Expected: CANNOT play - need 5 mana but only have 3 lands
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{4}{B}")
        
        # Mountain produces RED
        # B/R lands produce BLACK or RED
        # Total: 3 lands = can produce max 3 mana
        # Cost: 4 generic + 1 black = 5 mana needed
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        dual1 = create_land(21, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        dual2 = create_land(22, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)")
        
        game = create_game_with_player(1, hand=[spell], battlefield=[mountain, dual1, dual2])
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_explicit_colorless_not_from_basic_land(self):
        """
        Scenario: Spell costs {C}, player has 3 Mountains (no colorless)
        Expected: CANNOT play - Mountains don't produce colorless
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{C}")
        
        mountains = [create_land(20 + i, "Mountain", 1, "Basic Land — Mountain") for i in range(3)]
        
        game = create_game_with_player(1, hand=[spell], battlefield=mountains)
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_explicit_colorless_from_wastes(self):
        """
        Scenario: Spell costs {C}, player has 1 Wastes
        Expected: CAN play - Wastes produce colorless
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{C}")
        
        wastes = create_land(20, "Wastes", 1, "Basic Land — Wastes")
        
        game = create_game_with_player(1, hand=[spell], battlefield=[wastes])
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == True
    
    def test_mana_pool_plus_land(self):
        """
        Scenario: Spell costs {R}, player has 0 red in pool but 1 Mountain
        Expected: CAN play - can use land for red
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{R}")
        
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        
        # Pool has no red
        game = create_game_with_player(
            1, hand=[spell], battlefield=[mountain],
            mana_pool={ManaColor.WHITE: 1}  # Only white in pool
        )
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == True
    
    def test_cannot_use_wrong_color_from_pool(self):
        """
        Scenario: Spell costs {1}{U}, all lands tapped, pool has {B: 2} (black - wrong color)
        Expected: CANNOT play - can't use black mana for blue, no lands available
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{1}{U}")
        
        # All lands tapped
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain", is_tapped=True)
        dual1 = create_land(21, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)", is_tapped=True)
        dual2 = create_land(22, "Blood Crypt", 1, "Land — Swamp Mountain", "({T}: Add {B} or {R}.)", is_tapped=True)
        
        # Pool has 2 black - can't pay blue with black!
        game = create_game_with_player(
            1, hand=[spell], battlefield=[mountain, dual1, dual2],
            mana_pool={ManaColor.BLACK: 2}
        )
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_double_faced_card_checks_all_faces(self):
        """
        Scenario: DFC card Norman Osborn (front: {1}{U}, back: {1}{U}{B}{R})
        Pool has 2 black, 1 untapped Mountain (red)
        Expected: CANNOT play - neither face is affordable
        """
        commander = Card(
            id=30,
            card_scryfall_id="test-30",
            card_name="Norman Osborn // Green Goblin",
            mana_cost=None,
            cmc=None,
            type_line="Legendary Creature — Human",
            oracle_text=None,
            colors=None,
            power="4",
            toughness="4",
            keywords=None,
            image_uris=None,
            card_faces=[
                {"name": "Norman Osborn", "mana_cost": "{1}{U}", "type_line": "Legendary Creature — Human"},
                {"name": "Green Goblin", "mana_cost": "{1}{U}{B}{R}", "type_line": "Legendary Creature — Goblin"}
            ],
            zone=CardZone.COMMANDER,
            position=0,
            is_tapped=False,
            is_face_up=True,
            battlefield_x=None,
            battlefield_y=None,
            is_attacking=False,
            is_blocking=False,
            is_summoning_sick=True,
            damage_received=0,
            player_id=1,
        )
        
        mountain = create_land(20, "Mountain", 1, "Basic Land — Mountain", is_tapped=False)
        
        game = create_game_with_player(
            1, hand=[], battlefield=[mountain], commander=[commander],
            mana_pool={ManaColor.BLACK: 2}
        )
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        commander_play = next(p for p in valid_plays['plays'] if p['card_id'] == 30)
        assert commander_play['can_afford_mana'] == False
    
    def test_commander_cost_exceeds_available_lands(self):
        """
        Scenario: Commander costs {3}{W}{W}, player has 4 lands
        (2 white-producing, 2 colorless-producing)
        Expected: CANNOT play - need 5 mana but only 4 lands
        """
        commander = create_card(30, "Spider-Man", CardZone.COMMANDER, 1, "{3}{W}{W}")
        
        # Reliquary Tower - colorless, Eiganjo - white, Plains - white, Rogue's Passage - colorless
        reliquary = create_land(20, "Reliquary Tower", 1, "Land", oracle_text=None)
        eiganjo = create_land(21, "Eiganjo", 1, "Land", oracle_text="{T}: Add {W}.")
        plains = create_land(22, "Plains", 1, "Basic Land — Plains")
        rogue = create_land(23, "Rogue's Passage", 1, "Land", oracle_text=None)
        
        game = create_game_with_player(
            1, hand=[], battlefield=[reliquary, eiganjo, plains, rogue],
            commander=[commander]
        )
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        commander_play = next(p for p in valid_plays['plays'] if p['card_id'] == 30)
        assert commander_play['can_afford_mana'] == False
    
    def test_commander_cost_with_generic(self):
        """
        Scenario: Commander costs {W}{W}{3}, player has 2 white + 3 generic
        Expected: CAN play - can pay 2 white from pool, 3 generic from any lands
        """
        commander = create_card(30, "My Commander", CardZone.COMMANDER, 1, "{W}{W}{3}")
        
        # 5 lands
        lands = [create_land(20 + i, f"Land{i}", 1) for i in range(5)]
        
        # Pool has 2 white, 0 generic (generic is just unspent mana)
        game = create_game_with_player(
            1, hand=[], battlefield=lands, commander=[commander],
            mana_pool={ManaColor.WHITE: 2, ManaColor.COLORLESS: 2}
        )
        engine = GameEngine(game)
        
        # Try to play commander
        try:
            result = engine.play_card(30, CardZone.BATTLEFIELD)
            # Should succeed - pool has 2 white, can tap 3 lands for generic
            assert True
        except InsufficientResourcesError:
            pytest.fail("Should be able to play commander with {W}{W}{3}")
    
    def test_cannot_play_not_your_turn(self):
        """
        Scenario: Player tries to get valid plays on opponent's turn
        Expected: Should not show can_cast_spells
        """
        spell = create_card(10, "Test Spell", CardZone.HAND, 1, "{1}")
        land = create_land(20, "Mountain", 1)
        
        # Player 1 is NOT active (Player 2 is active)
        game = create_game_with_player(
            1, hand=[spell], battlefield=[land],
            is_active=False, phase=TurnPhase.MAIN1
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        # Should not be able to cast spells on opponent's turn
        assert valid_plays['can_cast_spells'] == False


# =============================================================================
# TEST: PLAY CARD (ACTUAL CASTING)
# =============================================================================

class TestPlayCard:
    """Tests for actual spell casting."""
    
    def test_play_creature_with_enough_mana(self):
        """
        Scenario: Cast 1R creature with 1 Mountain in pool
        Expected: Success, Mountain tapped
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{1}{R}")
        mountain = create_land(20, "Mountain", 1)
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[mountain],
            mana_pool={ManaColor.RED: 1}  # 1 red in pool
        )
        
        engine = GameEngine(game)
        result = engine.play_card(10, CardZone.BATTLEFIELD)
        
        assert result.success
        assert len(engine.game_state.players[0].hand) == 0
        assert len(engine.game_state.players[0].battlefield) == 2  # creature + land
    
    def test_play_with_generic_taps_any_land(self):
        """
        Scenario: Cast {1}{R} creature, no mana in pool, 2 Mountains
        Expected: Success - 1 land tapped for red, 1 for generic
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{1}{R}")
        mountain1 = create_land(20, "Mountain1", 1, "Basic Land — Mountain")
        mountain2 = create_land(21, "Mountain2", 1, "Basic Land — Mountain")
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[mountain1, mountain2],
            mana_pool={}  # No mana in pool
        )
        
        engine = GameEngine(game)
        result = engine.play_card(10, CardZone.BATTLEFIELD)
        
        assert result.success
        # Both lands should be tapped now
        assert mountain1.is_tapped
        assert mountain2.is_tapped
    
    def test_play_fails_insufficient_mana(self):
        """
        Scenario: Cast {R}{R} with only 1 red source available
        Expected: Failure
        """
        creature = create_card(10, "Dragon", CardZone.HAND, 1, "{R}{R}")
        mountain = create_land(20, "Mountain", 1)
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[mountain],
            mana_pool={}  # No mana in pool
        )
        
        engine = GameEngine(game)
        
        with pytest.raises(InsufficientResourcesError):
            engine.play_card(10, CardZone.BATTLEFIELD)
    
    def test_play_commander_from_commander_zone(self):
        """
        Scenario: Play commander from commander zone
        Expected: Success
        """
        commander = create_card(30, "My Commander", CardZone.COMMANDER, 1, "{W}{W}{3}")
        
        lands = [create_land(20 + i, f"Land{i}", 1) for i in range(5)]
        
        game = create_game_with_player(
            1, hand=[], battlefield=lands, commander=[commander],
            mana_pool={ManaColor.WHITE: 2, ManaColor.COLORLESS: 3}
        )
        
        engine = GameEngine(game)
        result = engine.play_card(30, CardZone.BATTLEFIELD)
        
        assert result.success


# =============================================================================
# TEST: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_tapped_lands_cannot_produce_mana(self):
        """
        Scenario: All lands are tapped, try to cast spell
        Expected: Cannot play
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{1}")
        land = create_land(20, "Mountain", 1, is_tapped=True)  # Tapped!
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[land],
            mana_pool={}
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == False
    
    def test_mixed_pool_and_land_payment(self):
        """
        Scenario: Pool has some mana, need to tap land for rest
        Expected: Success
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{2}{R}")
        
        # Pool has 1 red + 1 colorless
        # Need 1 more red from land
        land = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[land],
            mana_pool={ManaColor.RED: 1, ManaColor.COLORLESS: 1}
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        spell_play = next(p for p in valid_plays['plays'] if p['card_id'] == 10)
        assert spell_play['can_afford_mana'] == True
    
    def test_mana_pool_decreased_after_play(self):
        """
        Scenario: Pool has mana, play a spell that uses it
        Expected: Pool mana is decreased after playing
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{R}")
        land = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[land],
            mana_pool={ManaColor.RED: 1}
        )
        
        engine = GameEngine(game)
        
        player_before = engine.game_state.players[0]
        assert player_before.mana_pool.get(ManaColor.RED, 0) == 1
        
        engine.play_card(10, CardZone.BATTLEFIELD)
        
        player_after = engine.game_state.players[0]
        assert player_after.mana_pool.get(ManaColor.RED, 0) == 0
    
    def test_mana_pool_colorless_decreased_after_play(self):
        """
        Scenario: Pool has colorless mana, play a spell that uses it
        Expected: Pool colorless is decreased after playing
        """
        creature = create_card(10, "Goblin", CardZone.HAND, 1, "{1}")
        land = create_land(20, "Mountain", 1, "Basic Land — Mountain")
        
        game = create_game_with_player(
            1, hand=[creature], battlefield=[land],
            mana_pool={ManaColor.COLORLESS: 2}
        )
        
        engine = GameEngine(game)
        
        player_before = engine.game_state.players[0]
        assert player_before.mana_pool.get(ManaColor.COLORLESS, 0) == 2
        
        engine.play_card(10, CardZone.BATTLEFIELD)
        
        player_after = engine.game_state.players[0]
        assert player_after.mana_pool.get(ManaColor.COLORLESS, 0) == 1
    
    def test_only_active_player_can_cast(self):
        """
        Scenario: Non-active player tries to get valid plays
        Expected: can_cast_spells is False
        """
        spell = create_card(10, "Spell", CardZone.HAND, 1, "{1}")
        land = create_land(20, "Mountain", 1)
        
        game = create_game_with_player(
            1, hand=[spell], battlefield=[land],
            is_active=False, phase=TurnPhase.MAIN1
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        assert valid_plays['can_cast_spells'] == False
    
    def test_can_only_play_land_main_phase(self):
        """
        Scenario: Try to play land during combat
        Expected: Cannot play land
        """
        land = create_card(10, "Forest", CardZone.HAND, 1, None, "Land")
        
        game = create_game_with_player(
            1, hand=[land], battlefield=[],
            phase=TurnPhase.COMBAT_ATTACK
        )
        
        engine = GameEngine(game)
        valid_plays = engine.get_valid_plays(1)
        
        assert valid_plays['can_play_land'] == False


# =============================================================================
# TEST: RUN ALL TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
