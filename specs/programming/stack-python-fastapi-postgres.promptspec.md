## Tech Stack: Python + FastAPI + PostgreSQL

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI with Pydantic v2 models for request/response validation
- **ORM**: SQLAlchemy 2.0 with async engine (asyncpg driver)
- **Migrations**: Alembic with auto-generate from models
- **Authentication**: JWT access tokens (15 min) + refresh tokens (7 days), stored in httpOnly cookies
- **Password hashing**: bcrypt via passlib, minimum 12 rounds
- **Task queue**: Celery with Redis broker (for background jobs)
- **Caching**: Redis with structured key namespaces (`app:entity:id:field`)

### Database
- **Engine**: PostgreSQL 16+
- **Connection pooling**: asyncpg pool, min 5 / max 20 connections
- **Naming conventions**: snake_case tables, plural nouns (e.g., `accounts`, `transactions`)
- **Soft deletes**: `deleted_at TIMESTAMP NULL` column; queries MUST filter `WHERE deleted_at IS NULL`
- **Audit columns**: every table MUST have `created_at`, `updated_at` (auto-managed)

### Testing
- **Framework**: pytest with pytest-asyncio
- **Coverage**: minimum 80% line coverage, 100% on business logic
- **Fixtures**: factory_boy for model factories, httpx.AsyncClient for API tests

### Deployment
- **Container**: Docker with multi-stage build (builder → slim runtime)
- **Config**: environment variables via pydantic-settings, `.env` for local dev
- **Health check**: `GET /health` returning `{"status": "ok", "version": "...", "db": "connected"}`
