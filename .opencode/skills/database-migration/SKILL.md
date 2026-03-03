# Database Migration

Manages Alembic database migrations for the Commander MTG backend.

## Commands

### Run All Pending Migrations

```bash
cd backend && make migrate
```

### Create a New Migration

```bash
cd backend && make migrate-create
```

This will prompt for a migration message. The command runs:

```bash
USE_SQLITE=true uv run alembic revision --autogenerate -m "your message"
```

### Create Migration Manually

```bash
cd backend && USE_SQLITE=true uv run alembic revision --autogenerate -m "description of changes"
```

### Upgrade to Specific Revision

```bash
cd backend && USE_SQLITE=true uv run alembic upgrade <revision>
```

### Downgrade One Version

```bash
cd backend && USE_SQLITE=true uv run alembic downgrade -1
```

### Show Current Revision

```bash
cd backend && USE_SQLITE=true uv run alembic current
```

### Show Migration History

```bash
cd backend && USE_SQLITE=true uv run alembic history
```

## Description

- Uses Alembic for SQLAlchemy database migrations
- Automatically uses SQLite when `USE_SQLITE=true` is set
- Migrations are stored in `backend/alembic/versions/`

## Common Workflow

```bash
# After making model changes, create a migration
cd backend && make migrate-create

# Run the migration
cd backend && make migrate

# Or do both in one command
cd backend && USE_SQLITE=true uv run alembic revision --autogenerate -m "your changes" && make migrate
```

## Environment Variables

- `USE_SQLITE=true` - Use SQLite instead of PostgreSQL for local development
