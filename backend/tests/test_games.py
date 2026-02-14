"""Tests for game room API."""
import pytest

COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"


class TestGameRoomCRUD:
    """Test game room CRUD operations."""

    def test_create_game(self, client, test_user):
        """Test creating a new game room."""
        game_data = {
            "name": "Test Game",
            "description": "A test game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }

        response = client.post("/api/v1/games", json=game_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Game"
        assert data["description"] == "A test game"
        assert data["is_public"] is True
        assert data["max_players"] == 4
        assert data["power_bracket"] == "casual"
        assert data["status"] == "waiting"
        assert data["invite_code"] is not None
        assert len(data["players"]) == 1
        assert data["players"][0]["username"] == "testuser"
        assert data["players"][0]["is_host"] is True

    def test_create_game_defaults(self, client, test_user):
        """Test creating a game with default values."""
        game_data = {
            "name": "Minimal Game",
        }

        response = client.post("/api/v1/games", json=game_data)
        assert response.status_code == 201

        data = response.json()
        assert data["max_players"] == 4
        assert data["power_bracket"] == "casual"
        assert data["is_public"] is False

    def test_list_games_empty(self, client, test_user):
        """Test listing games when none exist."""
        response = client.get("/api/v1/games")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_list_games_with_public_game(self, client, test_user):
        """Test listing games includes public game."""
        game_data = {
            "name": "Public Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        client.post("/api/v1/games", json=game_data)

        response = client.get("/api/v1/games")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any(game["name"] == "Public Game" for game in data)

    def test_get_game(self, client, test_user):
        """Test getting a specific game."""
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

        data = response.json()
        assert data["id"] == game_id
        assert data["name"] == "Test Game"

    def test_get_game_by_invite_code(self, client, test_user):
        """Test getting a game by invite code."""
        game_data = {
            "name": "Invite Test Game",
            "is_public": False,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        invite_code = create_response.json()["invite_code"]

        response = client.get(f"/api/v1/games/invite/{invite_code}")
        assert response.status_code == 200

        data = response.json()
        assert data["invite_code"] == invite_code

    def test_get_game_not_found(self, client, test_user):
        """Test getting non-existent game returns 404."""
        response = client.get("/api/v1/games/99999")
        assert response.status_code == 404

    def test_delete_game_as_host(self, client, test_user):
        """Test host can delete their game."""
        game_data = {
            "name": "Deletable Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/games/{game_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/games/{game_id}")
        assert get_response.status_code == 404
