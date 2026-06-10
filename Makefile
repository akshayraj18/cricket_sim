.PHONY: install run kill test unit integration regression lint clean \
	backend-up backend-down backend-run backend-migrate backend-test

# Install/sync project + dev dependencies (pytest, pyflakes) via uv.
install:
	uv sync

# Start the legacy stdlib web UI at http://localhost:8765
run:
	uv run python3 legacy/ui_server.py

# Kill any running legacy/ui_server.py processes.
kill:
	pkill -f legacy/ui_server.py || true

# Run the full test suite (use `make test ARGS="-k impact_sub"` to filter).
test:
	uv run pytest $(ARGS)

# Run only fast, isolated unit tests (helpers, models, engine, players_data).
unit:
	uv run pytest -m unit $(ARGS)

# Run only integration tests (draft/lineup/match-flow/league-state/ui_server).
integration:
	uv run pytest -m integration $(ARGS)

# Run only regression tests (whole-career/season lifecycle).
regression:
	uv run pytest -m regression $(ARGS)

# Static-check for undefined names, unused imports, etc.
lint:
	uv run pyflakes packages/sim_engine/src/cricket_sim_engine legacy tests backend/app backend/tests

# Remove cached bytecode.
clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete

# --- FastAPI backend (Postgres + Redis via Docker, see backend/) ---------------

# Start Postgres + Redis containers for the backend.
backend-up:
	cd backend && docker compose up -d

# Stop the backend's Postgres + Redis containers.
backend-down:
	cd backend && docker compose down

# Apply Alembic migrations to the local backend database.
backend-migrate:
	cd backend && uv run alembic upgrade head

# Start the FastAPI dev server at http://localhost:8000
backend-run:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run backend tests against the local Postgres container (requires backend-up).
backend-test:
	cd backend && uv run pytest tests/ $(ARGS)
