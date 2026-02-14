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


class TestGameJoin:
    """Test game join functionality."""

    def test_join_game_as_host_fails(self, client, test_user):
        """Test host cannot join their own game."""
        game_data = {
            "name": "Joinable Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/join")
        assert response.status_code == 400
        assert "already in this game" in response.json()["detail"].lower()

    def test_join_game_not_found(self, client, test_user):
        """Test joining non-existent game returns 404."""
        response = client.post("/api/v1/games/99999/join")
        assert response.status_code == 404


class TestGamePlayerManagement:
    """Test player acceptance and rejection."""

    def test_accept_nonexistent_player(self, client, test_user):
        """Test accepting a non-existent player returns 404."""
        game_data = {
            "name": "Accept Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/accept/99999")
        assert response.status_code == 404

    def test_reject_nonexistent_player(self, client, test_user):
        """Test rejecting a non-existent player returns 404."""
        game_data = {
            "name": "Reject Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/reject/99999")
        assert response.status_code == 404

    def test_accept_player_not_pending(self, client, test_user):
        """Test accepting an already accepted player fails."""
        game_data = {
            "name": "Already Accepted Test",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.get(f"/api/v1/games/{game_id}")
        host_player_id = None
        for player in response.json().get("players", []):
            if player.get("is_host"):
                host_player_id = player.get("id")
                break

        if host_player_id:
            response = client.post(f"/api/v1/games/{game_id}/accept/{host_player_id}")
            assert response.status_code == 400


class TestGameLeave:
    """Test leaving a game."""

    def test_host_cannot_leave_game(self, client, test_user):
        """Test host cannot leave, must delete instead."""
        game_data = {
            "name": "Host Leave Test",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/games/{game_id}/leave")
        assert response.status_code == 400
        assert "Host cannot leave" in response.json()["detail"]

    def test_leave_nonexistent_game(self, client, test_user):
        """Test leaving a nonexistent game returns 404."""
        response = client.delete("/api/v1/games/99999/leave")
        assert response.status_code == 404


class TestGameStartStop:
    """Test game start and stop."""

    def test_start_game_not_enough_players(self, client, test_user):
        """Test starting game with less than 2 players fails."""
        game_data = {
            "name": "Solo Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/start")
        assert response.status_code == 400
        assert "Need at least 2 players" in response.json()["detail"]

    def test_stop_game_not_in_progress(self, client, test_user):
        """Test stopping a game that is not in progress fails."""
        game_data = {
            "name": "Stop Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/stop")
        assert response.status_code == 400
        assert "Game is not in progress" in response.json()["detail"]


class TestDeckSelection:
    """Test deck selection for games."""

    def test_select_deck_for_game(self, client, test_user):
        """Test selecting a deck for a game."""
        deck_data = {
            "name": "Test Deck for Game",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        deck_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = deck_response.json()["id"]

        game_data = {
            "name": "Deck Select Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        game_response = client.post("/api/v1/games", json=game_data)
        game_id = game_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/select-deck", json={
            "deck_id": deck_id
        })
        assert response.status_code == 200

        data = response.json()
        player_with_deck = [p for p in data["players"] if p.get("deck_id") == deck_id]
        assert len(player_with_deck) == 1

    def test_select_deck_not_owner(self, client, test_user):
        """Test selecting a deck you don't own fails."""
        game_data = {
            "name": "Deck Ownership Test",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        game_response = client.post("/api/v1/games", json=game_data)
        game_id = game_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/select-deck", json={
            "deck_id": 99999
        })
        assert response.status_code == 404
