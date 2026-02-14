"""Tests for authentication API."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

os.environ["USE_SQLITE"] = "true"

from app.main import app
from app.core.database import get_db, Base
from app.core.auth import get_current_user
from app.models import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_client(test_user):
    """Client with authenticated user."""
    async def _override_get_current_user():
        db = TestingSessionLocal()
        try:
            user = db.query(User).filter(User.id == test_user.id).first()
            return user
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = override_get_db

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class TestLogin:
    """Test user login."""

    def test_login_invalid_credentials(self, auth_client):
        """Test login with invalid credentials fails."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.authenticate_user.return_value = None
            mock_get_service.return_value = mock_service

            response = auth_client.post("/api/v1/login", json={
                "email": "wrong@example.com",
                "password": "wrongpassword"
            })
            assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh."""

    def test_refresh_token_invalid(self, auth_client):
        """Test refresh with invalid token fails."""
        with patch('app.core.security.verify_token') as mock_verify:
            mock_verify.return_value = None

            response = auth_client.post("/api/v1/refresh", json={
                "refresh_token": "invalid_token"
            })
            assert response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints."""

    def test_get_current_user_profile(self, auth_client):
        """Test getting current user profile."""
        response = auth_client.get("/api/v1/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_update_profile(self, auth_client):
        """Test updating user profile."""
        response = auth_client.put("/api/v1/me", json={
            "display_name": "Updated Name"
        })
        assert response.status_code == 200


class TestPasswordChange:
    """Test password change."""

    def test_change_password_invalid_current_password(self, auth_client):
        """Test password change with wrong current password."""
        response = auth_client.post("/api/v1/change-password", json={
            "current_password": "wrongpassword",
            "new_password": "NewPass123!",
            "confirm_password": "NewPass123!"
        })
        assert response.status_code == 400


class TestLogout:
    """Test logout."""

    def test_logout_success(self, auth_client):
        """Test successful logout."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.revoke_all_sessions.return_value = 1
            mock_get_service.return_value = mock_service

            response = auth_client.post("/api/v1/logout")
            assert response.status_code == 200
            assert "successfully" in response.json()["message"].lower()


class TestValidation:
    """Test validation endpoints."""

    def test_validate_email_available(self, auth_client):
        """Test email validation - available."""
        response = auth_client.post("/api/v1/validate-email?email=available@example.com")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["is_available"] is True

    def test_validate_username(self, auth_client):
        """Test username validation."""
        response = auth_client.post("/api/v1/validate-username?username=testuser")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_validate_username_too_short(self, auth_client):
        """Test username too short."""
        response = auth_client.post("/api/v1/validate-username?username=ab")
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False

    def test_check_password_strength_strong(self, auth_client):
        """Test password strength check - strong password."""
        response = auth_client.post("/api/v1/check-password-strength?password=VeryStrongPassword123!")
        assert response.status_code == 200
        data = response.json()
        assert data["strength"] in ["strong", "medium", "Strong", "Medium"]


class TestSessions:
    """Test session management."""

    def test_get_user_sessions(self, auth_client):
        """Test getting user sessions."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_active_sessions_count.return_value = 1
            mock_get_service.return_value = mock_service

            response = auth_client.get("/api/v1/sessions")
            assert response.status_code == 200
            data = response.json()
            assert "active_sessions" in data

    def test_revoke_all_sessions(self, auth_client):
        """Test revoking all sessions."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.revoke_all_sessions.return_value = 2
            mock_get_service.return_value = mock_service

            response = auth_client.delete("/api/v1/sessions")
            assert response.status_code == 200
            assert "Revoked" in response.json()["message"]


class TestRegistration:
    """Test user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "newuser@example.com"
            mock_user.username = "newuser"
            mock_service.create_user.return_value = mock_user
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/register", json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            })
            assert response.status_code == 201

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email fails."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_user.side_effect = ValueError("Email already registered")
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/register", json={
                "email": "existing@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!"
            })
            assert response.status_code == 400

    def test_register_passwords_not_match(self, client):
        """Test registration with non-matching passwords fails."""
        response = client.post("/api/v1/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "confirm_password": "DifferentPass123!"
        })
        assert response.status_code == 422


class TestPasswordReset:
    """Test password reset."""

    def test_forgot_password_existing_user(self, client):
        """Test forgot password for existing user."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_user = MagicMock()
            mock_service.get_user_by_email.return_value = mock_user
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/forgot-password", params={"email": "test@example.com"})
            assert response.status_code == 200
            assert "If an account" in response.json()["message"]

    def test_forgot_password_nonexistent_user(self, client):
        """Test forgot password for non-existent user returns same response."""
        with patch('app.api.v1.auth.get_user_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_user_by_email.return_value = None
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/forgot-password", params={"email": "nonexistent@example.com"})
            assert response.status_code == 200
            assert "If an account" in response.json()["message"]

    def test_reset_password_invalid_token(self, client):
        """Test reset password with invalid token fails."""
        with patch('app.api.v1.auth.verify_password_reset_token') as mock_verify:
            mock_verify.return_value = None

            response = client.post("/api/v1/reset-password", json={
                "token": "invalid_token",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!"
            })
            assert response.status_code == 400
