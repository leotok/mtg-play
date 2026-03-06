# AGENTS.md - Agentic Coding Guidelines

This file provides guidelines for agentic coding agents operating in this repository.

## Project Overview

MTG Commander Online Platform - A web-based platform for playing Magic: The Gathering Commander games online with 4 players in real-time.

- **Backend**: Python 3.13+ with **uv** package manager, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 19 with TypeScript, Vite, Zustand

---

## Build/Lint/Test Commands

### Quick Reference

```bash
# Full setup (recommended)
make dev-setup

# Backend
make backend-dev          # Start backend dev server
make backend-test         # Run all backend tests
make migrate              # Run database migrations

# Frontend
make frontend-dev         # Start frontend dev server
make frontend-test       # Run frontend tests
make frontend-build      # Build for production
```

### Running a Single Test

**Backend (pytest with uv):**
```bash
cd backend
USE_SQLITE=true uv run pytest tests/test_auth.py::test_register -v
USE_SQLITE=true uv run pytest tests/test_engine.py::test_specific_function -v
```

**Frontend (vitest):**
```bash
cd frontend
npm run test:run -- --testNamePattern="test name"
npm run test:run src/services/apiClient.test.ts
```

### Linting & Formatting

```bash
# All linting
make lint

# Backend only
cd backend && uv run ruff check .

# Backend formatting
cd backend && uv run ruff format .

# Frontend only
cd frontend && npm run lint
```

### Database Migrations

```bash
cd backend
USE_SQLITE=true uv run alembic revision --autogenerate -m "description"
USE_SQLITE=true uv run alembic upgrade head
USE_SQLITE=true uv run alembic downgrade -1
```

---

## Code Style Guidelines

### Backend (Python)

**Imports:**
- Standard library first, then third-party, then local
- Use explicit relative imports from `app` package
- Example: `from app.core.security import create_access_token`

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `GameService`, `UserRepository`)
- Functions/methods: `snake_case` (e.g., `get_user_service`, `create_engine_from_db`)
- Variables: `snake_case` (e.g., `game_repo`, `user_data`)
- Constants: `UPPER_SNAKE_CASE`
- Database models: `PascalCase` (SQLAlchemy convention)
- Pydantic schemas: `PascalCase` with `Response`, `Create`, `Update` suffixes

**Types:**
- Use Python 3.13+ type hints
- Use `Optional[X]` instead of `X | None`
- Use Pydantic for request/response schemas
- Use SQLAlchemy models for database entities

**Error Handling:**
- Use `HTTPException` for HTTP errors with appropriate status codes
- Log errors with `logger = logging.getLogger(__name__)` 
- Include error context in log messages
- Catch specific exceptions before generic `Exception`
- Example pattern:
  ```python
  try:
      user = user_service.create_user(user_data)
  except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
  except Exception as e:
      logger.error(f"Unexpected error: {e}", exc_info=True)
      raise HTTPException(status_code=500, detail="Internal error")
  ```

**API Routes:**
- Use ` with prefix (APIRouter`e.g., `/api/v1/auth`)
- Use async/await for route handlers
- Dependency injection for services via `Depends()`

**Database:**
- Use repositories for data access
- Use sessions with context managers
- Follow repository pattern from `app.repositories`

---

### Frontend (React + TypeScript)

**Imports:**
- React imports first, then third-party, then local
- Use explicit file extensions (`.tsx` for components, `.ts` for utilities)
- Group: external libs → internal libs → components/types → utilities
- Example:
  ```typescript
  import React, { useState, useEffect } from 'react';
  import { useNavigate } from 'react-router-dom';
  import { useAuthStore } from '../store/authStore';
  import { type User } from '../types/auth';
  import { Card } from './Card';
  ```

**Naming Conventions:**
- Components: `PascalCase` (e.g., `GameSideBar`, `CardList`)
- Files: `kebab-case.ts(x)` (e.g., `game-page.tsx`, `auth-context.tsx`)
- Hooks: `camelCase` starting with `use` (e.g., `useAuth`, `useGameState`)
- Types/Interfaces: `PascalCase` (e.g., `GameCard`, `UserState`)
- Constants: `UPPER_SNAKE_CASE` or `camelCase` for config

**Types:**
- Always define explicit types for props, state, and API responses
- Use `interface` for public APIs, `type` for unions/intersections
- Use `React.FC<Props>` for functional components
- Avoid `any` - use `unknown` when type is truly unknown

**State Management:**
- Use Zustand for global state
- Use local `useState` for component-specific state
- Use `useEffect` for side effects with proper cleanup

**Components:**
- Use functional components with arrow functions or `function` keyword
- Destructure props in component signature
- Keep components focused and small
- Extract reusable logic into custom hooks

**Error Handling:**
- Handle API errors with try/catch
- Show user-friendly error messages via Toast/notification system
- Log errors to console or error tracking service

---

## Project Structure

```
commander/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API route handlers
│   │   ├── core/            # Core utilities (auth, config, database)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── engine/          # Game engine logic
│   │   └── websocket/       # Socket.IO handlers
│   ├── tests/               # Backend tests
│   └── alembic/             # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── store/          # Zustand stores
│   │   ├── services/       # API clients
│   │   ├── types/          # TypeScript types
│   │   ├── schemas/        # Zod schemas
│   │   └── utils/          # Utility functions
│   └── tests/              # Frontend tests
└── Makefile                # Development commands
```

---

## Testing Guidelines

### Backend Tests
- Use pytest with fixtures from `conftest.py`
- Use `USE_SQLITE=true` environment variable for tests
- Mock external services (Scryfall API, Redis)
- Test both success and error cases

### Frontend Tests
- Use vitest with React Testing Library
- Mock API calls with appropriate responses
- Test component rendering and user interactions
- Use `@testing-library/jest-dom` for DOM assertions

---

## Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
USE_SQLITE=true  # For development/testing
```

**Frontend:** Uses `src/config.ts` for configuration.

---

## Common Development Workflows

1. **Creating a new API endpoint:**
   - Add route in `app/api/v1/<module>.py`
   - Add Pydantic schemas in `app/schemas/<module>.py`
   - Add service logic in `app/services/<module>_service.py`
   - Add tests in `tests/test_<module>.py`

2. **Creating a new frontend feature:**
   - Add types in `types/<feature>.ts`
   - Add API client methods in `services/apiClient.ts`
   - Create components in `components/<feature>/`
   - Add page in `pages/`
   - Add tests in `tests/`

3. **Database changes:**
   - Create migration: `uv run alembic revision --autogenerate -m "description"`
   - Edit migration file if needed
   - Apply: `uv run alembic upgrade head`
