"""Tests for deck import API."""
import pytest
from unittest.mock import AsyncMock

COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"
CARD_SCRYFALL_ID = "test-card-scryfall-id"


class TestSimpleDeckImport:
    """Test simple deck import endpoint."""

    def test_import_deck_basic(self, client, test_user, mock_scryfall):
        """Test basic deck import."""
        import_data = {
            "name": "Imported Deck",
            "description": "Test import",
            "commander": "Test Commander",
            "cards": ["Test Card"],
            "is_public": False,
        }

        response = client.post("/api/v1/simple_deck_import", json=import_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["deck_name"] == "Imported Deck"
        assert data["deck_id"] is not None
        assert data["total_cards"] == 2  # Commander + 1 card

    def test_import_deck_with_quantities(self, client, test_user, mock_scryfall):
        """Test deck import preserves card quantities."""
        import_data = {
            "name": "Quantity Test Deck",
            "commander": "Test Commander",
            "cards": [
                "Test Card",
                "Test Card",
                "Test Card",
            ],
            "is_public": False,
        }

        response = client.post("/api/v1/simple_deck_import", json=import_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True

        imported_cards = [c for c in data["imported_cards"] if not c["is_commander"]]
        assert len(imported_cards) == 1
        assert imported_cards[0]["quantity"] == 3
        assert data["total_cards"] == 4  # Commander + 3 cards

    def test_import_deck_multiple_different_cards_with_quantities(self, client, test_user, mock_scryfall):
        """Test import with multiple different cards, each with their own quantity."""
        import_data = {
            "name": "Multi Card Deck",
            "commander": "Test Commander",
            "cards": [
                "Test Card", "Test Card",  # 2x
                "Plains", "Plains", "Plains", "Plains",  # 4x
            ],
            "is_public": False,
        }

        response = client.post("/api/v1/simple_deck_import", json=import_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is True
        assert data["total_cards"] == 7  # Commander + 2 + 4

    def test_import_deck_commander_not_found(self, client, test_user, mock_scryfall):
        """Test import fails when commander not found."""
        mock_scryfall.get_card_by_name = AsyncMock(return_value=None)

        import_data = {
            "name": "Bad Commander Deck",
            "commander": "NonExistent Commander",
            "cards": ["Test Card"],
            "is_public": False,
        }

        response = client.post("/api/v1/simple_deck_import", json=import_data)
        assert response.status_code == 201

        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
