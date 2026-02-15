"""Tests for game state API - simplified version."""
import pytest
from unittest.mock import patch, MagicMock


COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"
CARD_SCRYFALL_ID = "test-card-scryfall-id"
PLAINS_SCRYFALL_ID = "test-plains-scryfall-id"


class TestGameStateAPI:
    """Test game state API endpoints."""

    def test_get_game_state_not_found(self, client, test_user):
        """Test getting game state when game doesn't exist returns 404."""
        response = client.get("/api/v1/games/99999/state")
        assert response.status_code == 404

    def test_get_game_state_not_started(self, client, test_user):
        """Test getting game state when game hasn't started."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.get(f"/api/v1/games/{game_id}/state")
        assert response.status_code == 404
        assert "Game state not found" in response.json()["detail"]


class TestGameStart:
    """Test starting a game with one player deck."""

    @pytest.fixture
    def setup_game(self, client, test_user, mock_scryfall):
        """Create a game with a deck and start it."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        deck_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = deck_response.json()["id"]

        for card_id in [PLAINS_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID, CARD_SCRYFALL_ID]:
            client.post(f"/api/v1/decks/{deck_id}/cards", json={
                "card_scryfall_id": card_id,
                "quantity": 1,
                "is_commander": False,
            })

        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 2,
            "power_bracket": "casual",
        }
        game_response = client.post("/api/v1/games", json=game_data)
        game_id = game_response.json()["id"]

        return {"game_id": game_id, "deck_id": deck_id}

    def test_start_game_without_players_fails(self, client, test_user, mock_scryfall, setup_game):
        """Test starting game with only one player fails."""
        game_id = setup_game["game_id"]
        
        response = client.post(f"/api/v1/games/{game_id}/start")
        assert response.status_code == 400
        assert "Need at least 2 players" in response.json()["detail"]


class TestGameStateModel:
    """Test game state model structure."""

    def test_game_state_response_structure(self, client, test_user):
        """Test that game state response has correct structure."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.get(f"/api/v1/games/{game_id}")
        assert response.status_code == 200
        
        game = response.json()
        assert "status" in game
        assert game["status"] == "waiting"
