"""Pytest configuration and shared fixtures."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment before imports
os.environ["USE_SQLITE"] = "true"

from app.main import app
from app.core.database import get_db, Base
from app.core.auth import get_current_user
from app.models import User, Deck, DeckCard

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Mock Scryfall service - returns valid card data for test IDs
def create_mock_scryfall_service():
    mock = MagicMock()
    commander_data = {
        "id": "test-commander-scryfall-id",
        "name": "Test Commander",
        "mana_cost": "{2}{W}{U}{B}{R}{G}",
        "cmc": 6,
        "type_line": "Legendary Creature — Human Knight",
        "colors": ["W", "U", "B", "R", "G"],
        "color_identity": ["W", "U", "B", "R", "G"],
        "oracle_text": "Flying",
        "power": "5",
        "toughness": "5",
        "loyalty": None,
        "image_uris": {"normal": "http://example.com/commander.jpg"},
        "legalities": {"commander": "legal"},
    }
    card_data = {
        "id": "test-card-scryfall-id",
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
    plains_data = {
        "id": "test-plains-scryfall-id",
        "name": "Plains",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "Basic Land — Plains",
        "colors": [],
        "color_identity": ["W"],
        "oracle_text": None,
        "power": None,
        "toughness": None,
        "loyalty": None,
        "image_uris": None,
        "legalities": {"commander": "legal"},
    }
    island_data = {
        "id": "test-island-scryfall-id",
        "name": "Island",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "Basic Land — Island",
        "colors": [],
        "color_identity": ["U"],
        "oracle_text": None,
        "power": None,
        "toughness": None,
        "loyalty": None,
        "image_uris": None,
        "legalities": {"commander": "legal"},
    }
    swamp_data = {
        "id": "test-swamp-scryfall-id",
        "name": "Swamp",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "Basic Land — Swamp",
        "colors": [],
        "color_identity": ["B"],
        "oracle_text": None,
        "power": None,
        "toughness": None,
        "loyalty": None,
        "image_uris": None,
        "legalities": {"commander": "legal"},
    }
    mountain_data = {
        "id": "test-mountain-scryfall-id",
        "name": "Mountain",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "Basic Land — Mountain",
        "colors": [],
        "color_identity": ["R"],
        "oracle_text": None,
        "power": None,
        "toughness": None,
        "loyalty": None,
        "image_uris": None,
        "legalities": {"commander": "legal"},
    }
    forest_data = {
        "id": "test-forest-scryfall-id",
        "name": "Forest",
        "mana_cost": "",
        "cmc": 0,
        "type_line": "Basic Land — Forest",
        "colors": [],
        "color_identity": ["G"],
        "oracle_text": None,
        "power": None,
        "toughness": None,
        "loyalty": None,
        "image_uris": None,
        "legalities": {"commander": "legal"},
    }

    mock.validate_commander = AsyncMock(return_value={"valid": True, "card": commander_data})
    
    def get_card_by_id(card_id):
        if "commander" in str(card_id):
            return commander_data
        if "plains" in str(card_id).lower():
            return plains_data
        if "island" in str(card_id).lower():
            return island_data
        if "swamp" in str(card_id).lower():
            return swamp_data
        if "mountain" in str(card_id).lower():
            return mountain_data
        if "forest" in str(card_id).lower():
            return forest_data
        return card_data

    mock.get_card_by_scryfall_id = AsyncMock(side_effect=get_card_by_id)
    mock.get_card_by_name = AsyncMock(return_value=commander_data)
    mock.search_cards = AsyncMock(return_value=[])
    
    def get_multiple_cards(card_names, by_name=False):
        result = {}
        for name in card_names:
            name_lower = name.lower()
            if "commander" in name_lower:
                result[name] = commander_data
            elif name_lower == "test card":
                result[name] = card_data
            elif name_lower == "plains":
                result[name] = plains_data
            elif name_lower == "island":
                result[name] = island_data
            elif name_lower == "swamp":
                result[name] = swamp_data
            elif name_lower == "mountain":
                result[name] = mountain_data
            elif name_lower == "forest":
                result[name] = forest_data
            else:
                result[name] = card_data
        return result

    mock.get_multiple_cards = AsyncMock(side_effect=get_multiple_cards)
    return mock


@pytest.fixture(scope="module")
def mock_scryfall():
    """Patch Scryfall service for all tests."""
    mock = create_mock_scryfall_service()
    with patch("app.services.deck_service.get_scryfall_service", return_value=mock), \
         patch("app.services.scryfall.get_scryfall_service", return_value=mock), \
         patch("app.services.game_service.get_scryfall_service", return_value=mock), \
         patch("app.api.v1.decks.get_scryfall_service", return_value=mock), \
         patch("app.api.v1.cards.get_scryfall_service", return_value=mock):
        yield mock


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Create test database tables. Drop first to ensure clean state."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user(setup_test_database):
    """Create a test user."""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="module")
def test_user2(setup_test_database):
    """Create a second test user for player interaction tests."""
    db = TestingSessionLocal()
    user = User(
        email="test2@example.com",
        username="testuser2",
        hashed_password="hashed_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture(scope="module", autouse=True)
def override_auth(test_user):
    """Override get_current_user to return test user."""

    async def _override_get_current_user():
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.id == test_user.id).first()
            return user
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def as_user2():
    """Temporarily override auth to use test_user2."""
    async def _override_user2():
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.username == "testuser2").first()
            return user
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = _override_user2
    yield
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture(scope="module")
def client(mock_scryfall, setup_test_database):
    """Test client with db and auth overrides."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]
