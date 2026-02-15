# MTG Commander Online - Development Commands

.PHONY: help backend-start backend-stop backend-dev backend-test frontend-start frontend-dev frontend-test install-backend install-backend-deps install-frontend clean lint format check-deps

# Default target
help:
	@echo "MTG Commander Online - Development Commands"
	@echo ""
	@echo "Backend Commands:"
	@echo "  backend-start      Start backend server (production mode)"
	@echo "  backend-stop       Stop backend server"
	@echo "  backend-dev       Start backend server (development mode)"
	@echo "  backend-test      Run backend tests"
	@echo "  backend-shell     Start Python shell with app context"
	@echo "  migrate           Run database migrations"
	@echo "  migrate-create    Create new migration"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  frontend-start    Start frontend server"
	@echo "  frontend-dev     Start frontend development server"
	@echo "  frontend-build   Build frontend for production"
	@echo "  frontend-test    Run frontend tests"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install-backend   Install backend dependencies"
	@echo "  install-frontend  Install frontend dependencies"
	@echo "  setup             Full project setup"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean             Clean temporary files"
	@echo "  lint              Run linting"
	@echo "  format            Format code"
	@echo "  check-deps        Check dependencies"

# =============================================================================
# BACKEND COMMANDS
# =============================================================================

backend-start:
	@echo "🚀 Starting backend server..."
	cd backend && USE_SQLITE=true uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

backend-stop:
	@echo "🛑 Stopping backend server..."
	pkill -f "uvicorn app.main:app" || true

backend-dev:
	@echo "🔧 Starting backend in development mode..."
	cd backend && USE_SQLITE=true uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	@echo "🧪 Running backend tests..."
	cd backend && USE_SQLITE=true uv run pytest tests/ -v

backend-shell:
	@echo "🐍 Starting Python shell with app context..."
	cd backend && USE_SQLITE=true uv run python -c "from app.core.database import SessionLocal; from app.models import *; from app.services import *; print('🎯 MTG Commander Backend Shell'); print('Available: db, User, Card, Deck, DeckCard'); print('Example: db = SessionLocal()')"

migrate:
	@echo "📊 Running database migrations..."
	cd backend && USE_SQLITE=true uv run alembic upgrade head

migrate-create:
	@echo "📝 Creating new migration..."
	@read -p "Enter migration message: " msg; \
	cd backend && USE_SQLITE=true uv run alembic revision --autogenerate -m "$$msg"

# =============================================================================
# FRONTEND COMMANDS  
# =============================================================================

SHELL := /bin/bash

frontend-start:
	@echo "🚀 Starting frontend server..."
	cd frontend && npm start

frontend-dev:
	@echo "🔧 Starting frontend development server..."
	cd frontend && npm run dev

frontend-build:
	@echo "🏗️ Building frontend for production..."
	cd frontend && npm run build

frontend-test:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm run test:run

# =============================================================================
# SETUP COMMANDS
# =============================================================================

install-backend:
	@echo "📦 Installing backend dependencies..."
	cd backend && uv sync

install-backend-deps:
	@echo "📦 Installing additional backend dependencies..."
	cd backend && uv add httpx redis[hiredis] python-multipart

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install

setup: install-backend install-frontend
	@echo "✅ Project setup complete!"
	@echo "Run 'make migrate' to set up the database"
	@echo "Run 'make backend-dev' to start development server"

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

clean:
	@echo "🧹 Cleaning temporary files..."
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd backend && rm -rf .pytest_cache 2>/dev/null || true
	cd frontend && rm -rf node_modules/.cache 2>/dev/null || true
	cd frontend && rm -rf dist 2>/dev/null || true
	@echo "✅ Clean complete!"

lint:
	@echo "🔍 Running linting..."
	cd backend && uv run ruff check .
	cd frontend && npm run lint 2>/dev/null || echo "Frontend lint not configured"

format:
	@echo "✨ Formatting code..."
	cd backend && uv run ruff format .
	cd frontend && npm run format 2>/dev/null || echo "Frontend format not configured"

check-deps:
	@echo "🔍 Checking dependencies..."
	cd backend && uv tree
	cd frontend && npm list 2>/dev/null || echo "Frontend dependencies check failed"

# =============================================================================
# DEVELOPMENT WORKFLOWS
# =============================================================================

dev-setup: setup migrate
	@echo "🎯 Complete development setup!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make backend-dev' (terminal 1)"
	@echo "2. Run 'make frontend-dev' (terminal 2)"
	@echo "3. Open http://localhost:8000/docs for API docs"
	@echo "4. Open http://localhost:3000 for frontend"

quick-test: backend-dev
	@echo "🧪 Quick backend test..."
	@sleep 3
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Backend not responding"

api-test:
	@echo "🔬 Testing API endpoints..."
	@echo "Testing health..."
	@curl -s http://localhost:8000/health | python -m json.tool
	@echo ""
	@echo "Testing cache stats..."
	@curl -s http://localhost:8000/api/v1/cache/stats | python -m json.tool
	@echo ""
	@echo "Testing decks..."
	@curl -s http://localhost:8000/api/v1/decks | python -m json.tool

# =============================================================================
# DOCKER COMMANDS (if needed)
# =============================================================================

docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# =============================================================================
# PRODUCTION COMMANDS
# =============================================================================

prod-build:
	@echo "🏗️ Building for production..."
	cd frontend && npm run build
	@echo "✅ Frontend build complete!"

prod-deploy:
	@echo "🚀 Deploying to production..."
	@echo "TODO: Add deployment script"
	@echo "This would typically involve:"
	@echo "1. Building frontend"
	@echo "2. Running database migrations"
	@echo "3. Starting production servers"
	@echo "4. Running health checks"
