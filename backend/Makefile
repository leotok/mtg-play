# MTG Commander Backend - Development Commands
# Run from backend/ directory

.PHONY: help start stop dev test shell migrate migrate-create install clean lint format check-deps

# Default target
help:
	@echo "MTG Commander Backend - Development Commands"
	@echo ""
	@echo "Server:"
	@echo "  start       Start server (production mode)"
	@echo "  stop        Stop server"
	@echo "  dev         Start server (development mode with reload)"
	@echo ""
	@echo "Database:"
	@echo "  migrate     Run database migrations"
	@echo "  migrate-create  Create new migration"
	@echo ""
	@echo "Development:"
	@echo "  test        Run tests"
	@echo "  shell       Start Python shell with app context"
	@echo "  install     Install dependencies (uv sync)"
	@echo ""
	@echo "Code quality:"
	@echo "  lint        Run linting (ruff)"
	@echo "  format      Format code (ruff)"
	@echo "  clean       Remove cache and temp files"
	@echo ""
	@echo "Other:"
	@echo "  check-deps  Show dependency tree"

# =============================================================================
# SERVER
# =============================================================================

start:
	@echo "🚀 Starting backend server..."
	USE_SQLITE=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

stop:
	@echo "🛑 Stopping backend server..."
	@pkill -f "uvicorn app.main:app" || true

dev:
	@echo "🔧 Starting backend in development mode..."
	USE_SQLITE=true uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# DATABASE
# =============================================================================

migrate:
	@echo "📊 Running database migrations..."
	USE_SQLITE=true uv run alembic upgrade head

migrate-create:
	@echo "📝 Creating new migration..."
	@read -p "Enter migration message: " msg; \
	USE_SQLITE=true uv run alembic revision --autogenerate -m "$$msg"

# =============================================================================
# DEVELOPMENT
# =============================================================================

test:
	@echo "🧪 Running tests..."
	USE_SQLITE=true PYTHONPATH=. uv run pytest tests/ -v

shell:
	@echo "🐍 Starting Python shell with app context..."
	USE_SQLITE=true uv run python -c "from app.core.database import SessionLocal; from app.models import *; from app.services import *; print('🎯 MTG Commander Backend Shell'); print('Available: db, User, Deck, DeckCard'); print('Example: db = SessionLocal()')"

install:
	@echo "📦 Installing dependencies..."
	uv sync

# =============================================================================
# CODE QUALITY
# =============================================================================

lint:
	@echo "🔍 Running linting..."
	uv run ruff check .

format:
	@echo "✨ Formatting code..."
	uv run ruff format .

clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@echo "✅ Clean complete!"

check-deps:
	@echo "🔍 Dependency tree:"
	uv tree
