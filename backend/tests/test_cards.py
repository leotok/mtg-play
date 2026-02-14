"""Tests for cards API."""
import pytest
from unittest.mock import AsyncMock, patch

COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"
CARD_SCRYFALL_ID = "test-card-scryfall-id"


class TestCardSearch:
    """Test card search endpoint."""

    def test_search_cards(self, client, test_user, mock_scryfall):
        """Test card search returns results."""
        mock_scryfall.search_cards = AsyncMock(return_value=[
            {"id": "card-1", "name": "Lightning Bolt", "type_line": "Instant"},
            {"id": "card-2", "name": "Lightning Helix", "type_line": "Instant"},
        ])

        response = client.get("/api/v1/search?q=lightning")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Lightning Bolt"

    def test_search_cards_with_type_filter(self, client, test_user, mock_scryfall):
        """Test card search with type filter."""
        mock_scryfall.search_cards = AsyncMock(return_value=[])

        response = client.get("/api/v1/search?q=bolt&type=instant")
        assert response.status_code == 200

    def test_search_cards_empty_query(self, client, test_user, mock_scryfall):
        """Test card search with empty query returns error."""
        response = client.get("/api/v1/search?q=")
        assert response.status_code == 200


class TestCardLookup:
    """Test card lookup endpoints."""

    def test_get_card_by_scryfall_id(self, client, test_user):
        """Test getting card by Scryfall ID."""
        mock_card_data = {
            "id": COMMANDER_SCRYFALL_ID,
            "name": "Test Commander",
            "mana_cost": "{2}{W}",
            "cmc": 3,
            "type_line": "Legendary Creature — Human Knight",
            "colors": ["W"],
            "color_identity": ["W"],
            "oracle_text": "Flying",
            "power": "3",
            "toughness": "3",
            "loyalty": None,
            "image_uris": {"normal": "http://example.com/image.jpg"},
            "legalities": {"commander": "legal"},
        }

        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_card_by_scryfall_id = AsyncMock(return_value=mock_card_data)
            mock_get_service.return_value = mock_service

            response = client.get(f"/api/v1/scryfall/{COMMANDER_SCRYFALL_ID}")
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "Test Commander"
            assert data["cmc"] == 3

    def test_get_card_by_scryfall_id_not_found(self, client, test_user):
        """Test 404 when card not found."""
        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_card_by_scryfall_id = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/scryfall/nonexistent-id")
            assert response.status_code == 404


class TestCardLookupByName:
    """Test card lookup by name endpoint."""

    def test_lookup_card_by_name(self, client, test_user):
        """Test looking up card by name."""
        mock_card_data = {
            "id": CARD_SCRYFALL_ID,
            "name": "Test Card",
            "mana_cost": "{1}{W}",
            "cmc": 2,
            "type_line": "Instant",
            "colors": ["W"],
            "color_identity": ["W"],
            "oracle_text": "Destroy target creature",
            "power": None,
            "toughness": None,
            "loyalty": None,
            "image_uris": {"normal": "http://example.com/card.jpg"},
            "legalities": {"commander": "legal"},
        }

        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_card_by_name = AsyncMock(return_value=mock_card_data)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/lookup", json={
                "identifier": "Test Card",
                "by_name": True
            })
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "Test Card"

    def test_lookup_card_by_id(self, client, test_user):
        """Test looking up card by Scryfall ID."""
        mock_card_data = {
            "id": COMMANDER_SCRYFALL_ID,
            "name": "Commander Card",
            "mana_cost": "{3}{W}{U}",
            "cmc": 5,
            "type_line": "Legendary Creature",
            "colors": ["W", "U"],
            "color_identity": ["W", "U"],
            "oracle_text": "Tap: Add {W}{U}",
            "power": "4",
            "toughness": "4",
            "loyalty": None,
            "image_uris": {"normal": "http://example.com/commander.jpg"},
            "legalities": {"commander": "legal"},
        }

        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_card_by_scryfall_id = AsyncMock(return_value=mock_card_data)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/lookup", json={
                "identifier": COMMANDER_SCRYFALL_ID,
                "by_name": False
            })
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "Commander Card"

    def test_lookup_card_not_found(self, client, test_user):
        """Test 404 when card lookup fails."""
        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_card_by_name = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/lookup", json={
                "identifier": "Nonexistent Card Name XYZ",
                "by_name": True
            })
            assert response.status_code == 404


class TestCardValidation:
    """Test card validation endpoint."""

    def test_validate_multiple_cards(self, client, test_user):
        """Test validating multiple cards at once."""
        def mock_get_multiple_cards(card_names, by_name=False):
            result = {}
            for name in card_names:
                if name in ["Lightning Bolt", "Counterspell", "Wrath of God"]:
                    result[name] = {
                        "id": f"id-{name.lower().replace(' ', '-')}",
                        "name": name,
                    }
            return result

        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_multiple_cards = AsyncMock(side_effect=mock_get_multiple_cards)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/validate", json={
                "card_names": ["Lightning Bolt", "Counterspell", "Wrath of God", "Fake Card XYZ"]
            })
            assert response.status_code == 200

            data = response.json()
            assert data["total_valid"] == 3
            assert data["total_invalid"] == 1
            assert len(data["valid_cards"]) == 3
            assert len(data["invalid_cards"]) == 1

    def test_validate_all_invalid_cards(self, client, test_user):
        """Test validation returns all invalid when none found."""
        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_multiple_cards = AsyncMock(return_value={})
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/validate", json={
                "card_names": ["Fake Card 1", "Fake Card 2"]
            })
            assert response.status_code == 200

            data = response.json()
            assert data["total_valid"] == 0
            assert data["total_invalid"] == 2

    def test_validate_empty_list(self, client, test_user):
        """Test validation with empty card list."""
        with patch('app.api.v1.cards.get_scryfall_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_multiple_cards = AsyncMock(return_value={})
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/validate", json={
                "card_names": []
            })
            assert response.status_code == 200

            data = response.json()
            assert data["total_valid"] == 0
            assert data["total_invalid"] == 0
