# Локальна розробка

Поточний етап: **M1 Foundation**. Бізнес-модулі ще не реалізуються.

## Backend

```bash
cd backend
python -m venv .venv
# активуйте virtual environment
pip install -e ".[dev]"
ruff check .
mypy
pytest -q
uvicorn transport_erp.main:app --reload
```

Liveness: `GET http://localhost:8000/health/live`.

## Frontend

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run dev
```

Frontend: `http://localhost:3000`.

## Development Compose

```bash
docker compose -f infra/compose.dev.yml up --build
```

Сервіси:

- frontend — `localhost:3000`;
- backend — `localhost:8000`;
- PostgreSQL — `localhost:5432`.

Значення PostgreSQL у development Compose є локальними defaults і не призначені для production.

## Межі M1.1

У цьому milestone немає:

- business/domain models;
- Alembic migrations;
- auth/RBAC implementation;
- production secrets;
- production deployment configuration.

Вони реалізуються окремими M1 issues після відповідних quality gates.
