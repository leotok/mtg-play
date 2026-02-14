"""Tests for cache API."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestCacheStats:
    """Test cache stats endpoint."""

    def test_get_cache_stats_success(self, client, test_user):
        """Test getting cache statistics."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_cache_stats = AsyncMock(return_value={
                "hits": 100,
                "misses": 50,
                "cached": 150,
                "hit_rate": 0.667,
                "total_keys": 150,
                "memory_usage": "1.5MB",
                "connected_clients": "5",
                "redis_version": "7.0.0"
            })
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/stats")
            assert response.status_code == 200

            data = response.json()
            assert data["hits"] == 100
            assert data["cached"] == 150
            assert data["hit_rate"] == 0.667

    def test_get_cache_stats_unavailable(self, client, test_user):
        """Test cache stats when service unavailable."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_cache_stats = AsyncMock(return_value={
                "error": "Connection refused"
            })
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/stats")
            assert response.status_code == 500


class TestCacheReset:
    """Test cache reset/clear endpoints."""

    def test_reset_cache_success(self, client, test_user):
        """Test clearing all cache."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.clear_all = AsyncMock(return_value=50)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/reset")
            assert response.status_code == 200

            data = response.json()
            assert data["cleared_count"] == 50
            assert "50" in data["message"]

    def test_clear_cache_pattern(self, client, test_user):
        """Test clearing cache by pattern."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.clear_pattern = AsyncMock(return_value=10)
            mock_get_service.return_value = mock_service

            response = client.post("/api/v1/clear-pattern?pattern=card:*")
            assert response.status_code == 200

            data = response.json()
            assert data["cleared_count"] == 10


class TestCacheWarm:
    """Test cache warming endpoint."""

    def test_warm_cache_success(self, client, test_user, mock_scryfall):
        """Test warming cache with cards."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_cache, \
             patch('app.api.v1.cache.get_scryfall_service') as mock_get_scryfall:

            mock_service = MagicMock()
            mock_get_cache.return_value = mock_service

            mock_scryfall_service = MagicMock()
            mock_scryfall_service.get_multiple_cards = AsyncMock(return_value={
                "Lightning Bolt": {"id": "card-1", "name": "Lightning Bolt"},
                "Counterspell": {"id": "card-2", "name": "Counterspell"},
            })
            mock_get_scryfall.return_value = mock_scryfall_service

            response = client.post("/api/v1/warm", json={
                "card_names": ["Lightning Bolt", "Counterspell"],
                "by_name": True
            })
            assert response.status_code == 200

            data = response.json()
            assert data["warmed_cards"] == 2
            assert data["requested"] == 2

    def test_warm_cache_partial_failure(self, client, test_user, mock_scryfall):
        """Test warming cache with some failed cards."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_cache, \
             patch('app.api.v1.cache.get_scryfall_service') as mock_get_scryfall:

            mock_service = MagicMock()
            mock_get_cache.return_value = mock_service

            mock_scryfall_service = MagicMock()
            mock_scryfall_service.get_multiple_cards = AsyncMock(return_value={
                "Valid Card": {"id": "card-1", "name": "Valid Card"},
            })
            mock_get_scryfall.return_value = mock_scryfall_service

            response = client.post("/api/v1/warm", json={
                "card_names": ["Valid Card", "Invalid Card"],
                "by_name": True
            })
            assert response.status_code == 200

            data = response.json()
            assert data["warmed_cards"] == 1
            assert data["requested"] == 2
            assert "Invalid Card" in data["failed_cards"]


class TestCachePopular:
    """Test popular cards endpoint."""

    def test_get_popular_cards(self, client, test_user):
        """Test getting popular cards."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_popular_cards = AsyncMock(return_value=[
                "Lightning Bolt",
                "Counterspell",
                "Brainstorm"
            ])
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/popular")
            assert response.status_code == 200

            data = response.json()
            assert len(data) == 3
            assert "Lightning Bolt" in data

    def test_get_popular_cards_with_limit(self, client, test_user):
        """Test getting popular cards with limit."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_popular_cards = AsyncMock(return_value=[
                "Card1", "Card2"
            ])
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/popular?limit=2")
            assert response.status_code == 200


class TestCacheHealth:
    """Test cache health endpoint."""

    def test_cache_health_healthy(self, client, test_user):
        """Test cache health when healthy."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_cache_stats = AsyncMock(return_value={
                "hits": 100,
                "total_keys": 50,
                "memory_usage": "1MB",
                "connected_clients": "3"
            })
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["total_keys"] == 50

    def test_cache_health_unhealthy(self, client, test_user):
        """Test cache health when unhealthy."""
        with patch('app.api.v1.cache.get_cache_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_cache_stats = AsyncMock(return_value={
                "error": "Connection refused"
            })
            mock_get_service.return_value = mock_service

            response = client.get("/api/v1/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
