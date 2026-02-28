# MTG Commander Online Platform

A web-based platform for playing Magic: The Gathering Commander games online with 4 players in real-time.

## Project Structure

```
commander/
├── backend/           # Python FastAPI backend
├── frontend/          # React TypeScript frontend
├── docker-compose.yml # Local development services
└── README.md          # This file
```

## Tech Stack

### Backend
- **Python 3.13** with **uv** package manager
- **FastAPI** - Modern web framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Primary database
- **Redis** - Caching and sessions
- **python-socketio** - Real-time communication
- **Alembic** - Database migrations

### Frontend
- **React 19** with **TypeScript**
- **Vite** - Build tool
- **React Router** - Routing
- **Zustand** - State management
- **Socket.IO Client** - Real-time communication

## Prerequisites

- Python 3.13+
- uv (Python package manager)
- Docker and Docker Compose
- Node.js 18+ and npm

## Quick Start

### Using Makefile (Recommended)

```bash
make dev-setup          # Full setup (install deps + migrations)
make help              # View all available commands

# Or individually:
make setup             # Install all dependencies
make migrate           # Run database migrations
make backend-dev       # Start backend (terminal 1)
make frontend-dev      # Start frontend (terminal 2)
```

### Manual Setup

**Start services:**
- Docker: `docker compose up -d`
- Or local PostgreSQL + Redis

**Run backend:**
```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Run frontend:**
```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Creating Users

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePassword123!"
  }'
```

### Via the UI

Navigate to `http://localhost:5173` and use the registration form.

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'
```

This returns an access token and refresh token.

## Testing

### Backend Tests

```bash
cd backend
uv run pytest
```

### Frontend Tests

```bash
cd frontend
npm run test      # Watch mode
npm run test:run  # Single run
npm run test:ui   # UI mode
```

### Database Migrations

```bash
cd backend

# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Roadmap

### Phase 1: MVP - Foundation
- ✅ Project setup with FastAPI, React, Socket.IO
- ✅ Card system with Scryfall API integration
- ✅ User authentication and deck management
- ✅ Basic game engine (turns, phases, zones)
- ✅ Game lobby
- ✅ Game board UI with drag-and-drop
- ✅ Card multi-selection drag-and-drop
- Game action logs
- Use socket.io for real-time game state synchronization during gameplay

### Phase 2: Game Complexity
- Move validation
- Mana system
- Stack system and targeting
- Complex abilities (keywords, activated/triggered)
- Commander damage rules
- AI opponent

### Phase 3: Polish & Social
- User profiles and stats
- Game replay
- Spectator mode
- Game chat and emotes

See `commander-roadmap.md` for detailed milestones.

## License

This project is for educational purposes only. Magic: The Gathering is property of Wizards of the Coast.
