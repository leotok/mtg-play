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
    }
    card_data = {
        "id": "test-card-scryfall-id",
        "name": "Test Card",
        "mana_cost": "{1}{W}",
        "cmc": 2,
        "type_line": "Instant",
        "colors": ["W"],
        "color_identity": ["W"],
    }

    mock.validate_commander = AsyncMock(return_value={"valid": True, "card": commander_data})
    def get_card_by_id(card_id):
        if "commander" in str(card_id):
            return commander_data
        return card_data

    mock.get_card_by_scryfall_id = AsyncMock(side_effect=get_card_by_id)
    mock.get_card_by_name = AsyncMock(return_value=commander_data)
    mock.get_multiple_cards = AsyncMock(
        return_value={
            "test-commander-scryfall-id": commander_data,
            "test-card-scryfall-id": card_data,
        }
    )
    return mock


@pytest.fixture(scope="module")
def mock_scryfall():
    """Patch Scryfall service for all tests."""
    mock = create_mock_scryfall_service()
    with patch("app.services.deck_service.get_scryfall_service", return_value=mock):
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


@pytest.fixture(scope="module")
def client(mock_scryfall, setup_test_database):
    """Test client with db and auth overrides."""
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]
