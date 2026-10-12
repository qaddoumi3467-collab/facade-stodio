# Facade Studio

Our own software for designing and pricing aluminium windows, doors and
facades (in the spirit of Orgadata LogiKal).

**Stage 1 – profile and system catalog.** Keep profile systems, aluminium
profiles, glass types and hardware in a database, with English and Arabic
names, and work out the weight and price of a cut profile piece or a glass
pane. All sizes are in millimetres.

Later stages: element designer, cutting lists and bar optimization, pricing
and quotes, CNC / workshop export.

## Layout

| Folder      | What it is                                                    |
|-------------|---------------------------------------------------------------|
| `backend/`  | Python FastAPI service, PostgreSQL via SQLAlchemy + Alembic   |
| `frontend/` | React + TypeScript (Vite) screens, English / Arabic (RTL)     |

Weight and price formulas live in `backend/app/calculations.py` and are
covered by `backend/tests/test_calculations.py`.

## Running it locally

You need Docker, Python 3.11+ and Node 20+.

```bash
# 1. Database
docker compose up -d db
docker compose exec db createdb -U facade facade_test   # used by the tests

# 2. Back end (http://localhost:8000, API docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
python -m app.seed          # optional: sample catalog to try things out
uvicorn app.main:app --reload

# 3. Front end (http://localhost:5173)
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend && pytest        # needs the facade_test database from step 1
cd frontend && npm test
```

Changing a model? Create a migration with
`alembic revision --autogenerate -m "what changed"` and check it in.
