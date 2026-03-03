# Test & Lint

Runs tests and linting checks for the Commander MTG backend.

## Commands

### Run All Tests

```bash
cd backend && make test
```

### Run Backend Tests Only

```bash
cd backend && PYTHONPATH=. uv run pytest tests/ -v
```

### Run Engine Tests Only

```bash
cd backend && PYTHONPATH=. uv run pytest tests/test_engine.py -v
```

### Run Linting

```bash
cd backend && python3 -m ruff check .
```

### Run Linting on Specific File

```bash
cd backend && python3 -m ruff check app/services/game_service.py
```

### Fix Lint Issues Automatically

```bash
cd backend && python3 -m ruff check . --fix
```

### Format Code

```bash
cd backend && python3 -m ruff format .
```

## Description

- **Tests**: Runs all pytest tests in the `tests/` directory
- **Lint**: Uses ruff to check for code issues
- **Format**: Auto-formats code using ruff

## Common Workflow

```bash
# Run tests first
cd backend && make test

# If tests pass, run linting
python3 -m ruff check .

# Fix any issues
python3 -m ruff check . --fix
```
