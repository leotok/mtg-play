# MTG Commander Online Platform

A web-based platform for playing Magic: The Gathering Commander games online with 4 players in real-time.

## Project Structure

```
commander/
├── backend/          # Python FastAPI backend
├── frontend/         # React TypeScript frontend (to be initialized)
├── docker-compose.yml # Local development services
└── commander-roadmap.md # Detailed project roadmap
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

### Frontend (Pending Node.js installation)
- **React 18** with **TypeScript**
- **Vite** - Build tool
- **React Router** - Routing
- **Zustand** - State management
- **Socket.IO Client** - Real-time communication
- **DnD Kit** - Drag and drop functionality

## Getting Started

### Prerequisites
- ✅ Python 3.13+ 
- ✅ uv (Python package manager)
- ⏳ Docker and Docker Compose (needs installation)
- ✅ Node.js 18+ and npm

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies (already done with uv):
```bash
uv sync
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Start local services (PostgreSQL and Redis):
```bash
cd ..
docker-compose up -d
```

5. Run the FastAPI server:
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Frontend Setup (Pending)

Node.js needs to be installed before setting up the frontend. 

**Install Node.js:**
- Option 1: Using nvm (recommended)
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install --lts
  ```
- Option 2: Download from [nodejs.org](https://nodejs.org/)

After installing Node.js, the frontend will be initialized with Vite and React.

## Development

### Running Services

Start PostgreSQL and Redis:
```bash
docker-compose up -d
```

Stop services:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

### Database Migrations (Coming Soon)

Once Alembic is configured:
```bash
cd backend
uv run alembic upgrade head
```

## Project Roadmap

See `commander-roadmap.md` for the complete development roadmap covering:
- Phase 1: MVP Foundation (3-4 months)
- Phase 2: Game Complexity (3-4 months)
- Phase 3: Social & Polish (2-3 months)
- Phase 4: Advanced Features (Ongoing)

## Current Status

✅ Backend structure initialized with FastAPI and uv  
✅ All Python dependencies installed  
✅ FastAPI application configured with CORS and settings  
✅ Database models created (User, Card, Deck, DeckCard)  
✅ Alembic configured for database migrations  
✅ Docker Compose configuration for PostgreSQL and Redis  
✅ Frontend initialized with React + TypeScript + Vite  
✅ React Router configured for navigation  
✅ Zustand store set up for state management  
✅ Socket.IO services created for real-time communication  
✅ API service with authentication headers  
⏳ Docker installation (required to run PostgreSQL and Redis)  
⏳ Running initial database migration  
⏳ Authentication endpoints  
⏳ Scryfall API integration  
⏳ Game engine core

## Next Steps

1. **Install Docker Desktop** (required for PostgreSQL and Redis)
   - Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - After installation, run: `docker compose up -d`

2. **Run database migrations**
   ```bash
   cd backend
   uv run alembic upgrade head
   ```

3. **Start the development servers**
   - Backend: `cd backend && uv run uvicorn app.main:app --reload`
   - Frontend: `cd frontend && npm run dev`

4. **Implement authentication system**
   - Create auth endpoints (register, login, logout)
   - Add JWT token generation and validation
   - Build login/register pages

5. **Integrate Scryfall API**
   - Create service to sync card data
   - Build card search endpoint
   - Add card search UI

6. **Build deck management**
   - Create deck CRUD endpoints
   - Build deck builder interface
   - Add deck validation

7. **Develop game engine**
   - Implement game state management
   - Create turn system
   - Build game board UI

## Contributing

This is a personal/educational project. For commercial use, official licensing from Wizards of the Coast would be required.

## License

This project is for educational purposes only. Magic: The Gathering is property of Wizards of the Coast.
