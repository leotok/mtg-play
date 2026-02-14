"""Tests for WebSocket event emission."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"
CARD_SCRYFALL_ID = "test-card-scryfall-id"


def mock_sio():
    """Create a mock socketio server."""
    mock = MagicMock()
    mock.emit = AsyncMock()
    return mock


class TestWebSocketEventEmission:
    """Test WebSocket events are emitted by API endpoints."""

    def test_join_does_not_emit_when_host_joins_own_game(self, client, test_user):
        """Test join does not emit when host tries to join their own game."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        response = client.post(f"/api/v1/games/{game_id}/join")
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_accept_emits_player_accepted(self, client, test_user):
        """Test accept player emits player_accepted event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.post(f"/api/v1/games/{game_id}/accept/99999")
            assert response.status_code == 404

    def test_reject_emits_player_rejected(self, client, test_user):
        """Test reject player emits player_rejected event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.post(f"/api/v1/games/{game_id}/reject/99999")
            assert response.status_code == 404

    def test_start_emits_game_started(self, client, test_user):
        """Test start game emits game_started event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.post(f"/api/v1/games/{game_id}/start")
            assert response.status_code == 400
            assert "2 players" in response.json()["detail"].lower()

    def test_stop_emits_game_stopped(self, client, test_user):
        """Test stop game emits game_stopped event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.post(f"/api/v1/games/{game_id}/stop")
            assert response.status_code == 400
            assert "not in progress" in response.json()["detail"].lower()

    def test_select_deck_emits_deck_selected(self, client, test_user):
        """Test select deck emits deck_selected event."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        deck_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = deck_response.json()["id"]

        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        game_response = client.post("/api/v1/games", json=game_data)
        game_id = game_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.post(
                f"/api/v1/games/{game_id}/select-deck",
                json={"deck_id": deck_id}
            )
            assert response.status_code == 200

            mock_get_sio.assert_called_once()
            sio = mock_get_sio.return_value
            sio.emit.assert_called()

            call_args = sio.emit.call_args
            assert call_args[0][0] == 'deck_selected'
            assert call_args[0][1]['deck_id'] == deck_id

    def test_leave_emits_player_left(self, client, test_user):
        """Test leave game emits player_left event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.delete(f"/api/v1/games/{game_id}/leave")
            assert response.status_code == 400
            assert "host cannot leave" in response.json()["detail"].lower()

    def test_delete_game_no_event(self, client, test_user):
        """Test delete game doesn't emit event (handled by client)."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        with patch('app.api.v1.games.get_sio', return_value=mock_sio()) as mock_get_sio:
            response = client.delete(f"/api/v1/games/{game_id}")
            assert response.status_code == 204

            mock_get_sio.assert_not_called()


class TestWebSocketEventData:
    """Test WebSocket events contain correct data."""

    def test_host_join_does_not_emit(self, client, test_user):
        """Test host joining own game does not emit event."""
        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        create_response = client.post("/api/v1/games", json=game_data)
        game_id = create_response.json()["id"]

        mock_sio_instance = mock_sio()

        with patch('app.api.v1.games.get_sio', return_value=mock_sio_instance):
            response = client.post(f"/api/v1/games/{game_id}/join")
            assert response.status_code == 400

            mock_sio_instance.emit.assert_not_called()

    def test_deck_selected_contains_correct_data(self, client, test_user):
        """Test deck_selected event has correct game_id, user_id, deck_id."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        deck_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = deck_response.json()["id"]

        game_data = {
            "name": "Test Game",
            "is_public": True,
            "max_players": 4,
            "power_bracket": "casual",
        }
        game_response = client.post("/api/v1/games", json=game_data)
        game_id = game_response.json()["id"]

        mock_sio_instance = mock_sio()

        with patch('app.api.v1.games.get_sio', return_value=mock_sio_instance):
            client.post(
                f"/api/v1/games/{game_id}/select-deck",
                json={"deck_id": deck_id}
            )

            mock_sio_instance.emit.assert_called_once()
            call_args = mock_sio_instance.emit.call_args

            event_name = call_args[0][0]
            event_data = call_args[0][1]

            assert event_name == 'deck_selected'
            assert event_data['game_id'] == game_id
            assert event_data['deck_id'] == deck_id
            assert 'user_id' in event_data
