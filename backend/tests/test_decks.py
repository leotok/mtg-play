"""Tests for deck API - Scryfall-only approach."""
import pytest

# Test IDs for Scryfall mock
COMMANDER_SCRYFALL_ID = "test-commander-scryfall-id"
CARD_SCRYFALL_ID = "test-card-scryfall-id"


class TestDeckCRUD:
    """Test deck CRUD operations."""

    def test_create_deck(self, client, test_user):
        """Test creating a new deck."""
        deck_data = {
            "name": "Test Deck",
            "description": "A test deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }

        response = client.post("/api/v1/decks", json=deck_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Deck"
        assert data["description"] == "A test deck"
        assert data["commander_scryfall_id"] == COMMANDER_SCRYFALL_ID
        assert data["is_public"] is False
        assert data["id"] is not None

    def test_get_user_decks(self, client, test_user):
        """Test getting user's decks."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        client.post("/api/v1/decks", json=deck_data)

        response = client.get("/api/v1/decks")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any(deck["name"] == "Test Deck" for deck in data)

    def test_get_deck(self, client, test_user):
        """Test getting a specific deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.get(f"/api/v1/decks/{deck_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == deck_id
        assert data["name"] == "Test Deck"

    def test_update_deck(self, client, test_user):
        """Test updating a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        update_data = {
            "name": "Updated Deck",
            "description": "Updated description",
        }
        response = client.put(f"/api/v1/decks/{deck_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Deck"
        assert data["description"] == "Updated description"

    def test_delete_deck(self, client, test_user):
        """Test deleting a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/decks/{deck_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/decks/{deck_id}")
        assert get_response.status_code == 404


class TestDeckCards:
    """Test deck card management."""

    def test_add_card_to_deck(self, client, test_user):
        """Test adding a card to a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        card_data = {
            "card_scryfall_id": CARD_SCRYFALL_ID,
            "quantity": 1,
            "is_commander": False,
        }
        response = client.post(f"/api/v1/decks/{deck_id}/cards", json=card_data)
        assert response.status_code == 201

        data = response.json()
        assert data["card_scryfall_id"] == CARD_SCRYFALL_ID
        assert data["quantity"] == 1
        assert data["is_commander"] is False

    def test_get_deck_cards(self, client, test_user):
        """Test getting cards in a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        card_data = {
            "card_scryfall_id": CARD_SCRYFALL_ID,
            "quantity": 2,
            "is_commander": False,
        }
        client.post(f"/api/v1/decks/{deck_id}/cards", json=card_data)

        response = client.get(f"/api/v1/decks/{deck_id}/cards")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 2  # Commander + test card
        assert any(card["card_scryfall_id"] == CARD_SCRYFALL_ID for card in data)


class TestDeckValidation:
    """Test deck validation."""

    def test_validate_empty_deck(self, client, test_user):
        """Test validating an empty deck (only commander)."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.post(f"/api/v1/decks/{deck_id}/validate")
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False
        assert "Deck must have exactly 100 cards" in str(data["validation_errors"])

    def test_get_deck_stats(self, client, test_user):
        """Test getting deck statistics."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.get(f"/api/v1/decks/{deck_id}/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["deck_id"] == deck_id
        assert data["total_cards"] == 1  # Only commander
        assert data["commander_count"] == 1
        assert data["main_deck_count"] == 0
        assert data["is_complete"] is False


class TestDeckExport:
    """Test deck export functionality."""

    def test_export_deck(self, client, test_user):
        """Test exporting a deck."""
        deck_data = {
            "name": "Test Deck",
            "description": "Test export",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.get(f"/api/v1/decks/{deck_id}/export")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "commander_scryfall_id" in data
        assert "cards" in data
        assert data["name"] == "Test Deck"
        assert data["description"] == "Test export"


class TestDeckCardManagement:
    """Test deck card management endpoints."""

    def test_clear_deck_cards(self, client, test_user):
        """Test clearing all cards from a deck (except commander)."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        card_data = {
            "card_scryfall_id": CARD_SCRYFALL_ID,
            "quantity": 2,
            "is_commander": False,
        }
        client.post(f"/api/v1/decks/{deck_id}/cards", json=card_data)

        response = client.delete(f"/api/v1/decks/{deck_id}/cards")
        assert response.status_code == 204

        cards_response = client.get(f"/api/v1/decks/{deck_id}/cards")
        cards = cards_response.json()
        assert all(card["is_commander"] for card in cards)

    def test_remove_card_from_deck(self, client, test_user):
        """Test removing a specific card from a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        card_data = {
            "card_scryfall_id": CARD_SCRYFALL_ID,
            "quantity": 3,
            "is_commander": False,
        }
        add_response = client.post(f"/api/v1/decks/{deck_id}/cards", json=card_data)
        card_id = add_response.json()["id"]

        response = client.delete(f"/api/v1/decks/{deck_id}/cards/{card_id}")
        assert response.status_code == 204

    def test_update_card_quantity_in_deck(self, client, test_user):
        """Test updating a card's quantity in a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        card_data = {
            "card_scryfall_id": CARD_SCRYFALL_ID,
            "quantity": 1,
            "is_commander": False,
        }
        add_response = client.post(f"/api/v1/decks/{deck_id}/cards", json=card_data)
        card_id = add_response.json()["id"]

        update_data = {"quantity": 4}
        response = client.put(f"/api/v1/decks/{deck_id}/cards/{card_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 4

    def test_remove_nonexistent_card_from_deck(self, client, test_user):
        """Test removing a non-existent card from a deck."""
        deck_data = {
            "name": "Test Deck",
            "commander_scryfall_id": COMMANDER_SCRYFALL_ID,
            "is_public": False,
        }
        create_response = client.post("/api/v1/decks", json=deck_data)
        deck_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/decks/{deck_id}/cards/99999")
        assert response.status_code == 204
