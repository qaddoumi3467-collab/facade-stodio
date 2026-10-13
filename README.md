# Facade Studio

Our own software for designing and pricing aluminium windows, doors and
facades (in the spirit of Orgadata LogiKal).

**Stage 1 – profile and system catalog.** Keep profile systems, aluminium
profiles, glass types and hardware in a database, with English and Arabic
names, and work out the weight and price of a cut profile piece or a glass
pane. All sizes are in millimetres.

**Stage 2 – element designer.** Draw a window or door: set its outer size,
split it into columns (mullions) and rows (transoms), choose the system,
profiles and glass from the catalog, and give each field an opening type
(fixed, turn, tilt-turn, tilt, sliding). The drawing updates as you type,
with a cut list (lengths and cut angles) and a glass list, and elements are
saved in the database.

Later stages: cutting lists and bar optimization, pricing and quotes,
CNC / workshop export.

## Layout

| Folder      | What it is                                                    |
|-------------|---------------------------------------------------------------|
| `backend/`  | Python FastAPI service, PostgreSQL via SQLAlchemy + Alembic   |
| `frontend/` | React + TypeScript (Vite) screens, English / Arabic (RTL)     |

Weight and price formulas live in `backend/app/calculations.py` and are
covered by `backend/tests/test_calculations.py`. The designer's geometry and
cut lengths live in `backend/app/designer.py` (rules at the top of the file)
and are covered by `backend/tests/test_designer.py`.

The designer uses each profile's **height** as its visible face width, and
two values on each system: the **sash overlap** (how far a sash laps over
the frame opening on each side) and the **glass bite** (how far the glass
goes in under the profile on each side).

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
python -m app.import_catalog   # load real catalogues (Alupco Saraya, 45, 52, ALUPCOtherm 123 and 97 SL)
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
