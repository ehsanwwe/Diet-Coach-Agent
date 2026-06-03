# Diet Coach Agent — Backend

FastAPI + SQLAlchemy 2.x + Alembic + SQLite backend.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Setup

### 1. Copy environment file

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY` — generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `OPENCLAW_BASE_URL` — leave empty to use MockAIProvider (no AI key required for development)

### 2. Install dependencies

With uv (recommended):
```bash
uv sync
```

With pip:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Initialize the database

```bash
alembic upgrade head
```

This creates `app.db` (SQLite) with all 22 tables.

### 4. Start the development server

```bash
uvicorn app.main:app --reload
```

Server starts on http://localhost:8000
OpenAPI docs: http://localhost:8000/docs

## Database Migrations

| Command | Description |
|---------|-------------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade base` | Roll back all migrations (drops all tables) |
| `alembic downgrade -1` | Roll back one migration |
| `alembic revision --autogenerate -m "description"` | Create new migration from model changes |
| `alembic history` | View migration history |

### SQLite Safeguards

`alembic/env.py` has two mandatory flags:
- `render_as_batch=True` — required for `ALTER TABLE` operations on SQLite
- `compare_type=True` — detects column type changes during autogenerate

**Never remove these flags.**

## Environment Variables

See `backend/.env.example` for all variables with descriptions.

Key variables:
- `SECRET_KEY` — **Required.** App refuses to start without it.
- `OPENCLAW_BASE_URL` — Optional. Leave empty for MockAIProvider.
- `DATABASE_URL` — Defaults to `sqlite+pysqlite:///./app.db`
- `CORS_ORIGINS` — Comma-separated frontend origins

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # Route handlers (endpoints)
│   ├── core/            # Config, database, errors
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic v2 request/response schemas
│   ├── services/        # Business logic layer
│   └── repositories/    # Data access layer
├── alembic/             # Database migrations
│   └── versions/        # Migration files
├── alembic.ini          # Alembic config
└── pyproject.toml       # Python project manifest
```

## Technology Notes

- **SQLAlchemy 2.x ONLY**: Use `select()` + `session.execute()`. Never `session.query()`.
- **lazy="raise"**: All ORM relationships raise an error if accessed outside a session.
- **PyJWT** (not python-jose): `jwt.encode()` / `jwt.decode()` with HS256.
- **pydantic-settings**: All config via `Settings(BaseSettings)` in `app/core/config.py`.
