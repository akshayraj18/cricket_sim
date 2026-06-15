.PHONY: install run kill test unit integration regression lint clean \
	backend-up backend-down backend-run backend-migrate backend-test gen-secret \
	mobile mobile-install mobile-typecheck mobile-lint mobile-ios mobile-sim-open

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

# Generate a strong JWT secret and write it to backend/.env.local (gitignored).
# Run ONCE per environment — changing the secret invalidates all existing
# sessions (everyone gets logged out). In production, set JWT_SECRET via your
# host's secrets/env panel instead of a file.
gen-secret:
	@cd backend && uv run python -c "import secrets, pathlib; \
		p = pathlib.Path('.env.local'); \
		existing = p.read_text() if p.exists() else ''; \
		print('Refusing to overwrite an existing JWT_SECRET in .env.local — delete it first to rotate.') if 'JWT_SECRET=' in existing else \
		(p.open('a').write(('\n' if existing and not existing.endswith('\n') else '') + 'JWT_SECRET=' + secrets.token_urlsafe(48) + '\n'), print('Wrote a new JWT_SECRET to backend/.env.local (gitignored).'))"

# --- Expo mobile app (mobile/) -------------------------------------------------

# Newest installed nvm Node >= 20 (Expo/Metro requires >=20.19.4; the default
# shell may still resolve to an older Node). Picks the highest v20/v21/v22+ dir.
MOBILE_NODE_BIN := $(shell ls -d $(HOME)/.nvm/versions/node/v2[0-9]* 2>/dev/null | sort -V | tail -1)/bin

# Start the Expo dev client + Metro bundler on all interfaces (port 8081).
# Works for both a physical device on the same Wi-Fi (via the LAN IP) and the
# iOS Simulator / Android emulator (via 127.0.0.1). Do NOT use `--localhost`:
# it binds IPv6-only ([::1]) and the simulator's IPv4 (127.0.0.1) request is
# then refused. (use `make mobile ARGS="--clear"` to reset the bundler cache.)
mobile:
	cd mobile && PATH="$(MOBILE_NODE_BIN):$$PATH" npx expo start --dev-client --port 8081 $(ARGS)

# Point the booted iOS Simulator's dev client at 127.0.0.1:8081 and open it.
# Run `make mobile` first (in another shell), then this — handy when the dev
# client is stuck on a stale LAN-IP URL and shows "Could not connect".
mobile-sim-open:
	xcrun simctl openurl booted "cric-sim://expo-development-client/?url=http%3A%2F%2F127.0.0.1%3A8081"

# Build + run the native iOS dev client on a simulator. Needed after adding a
# native module / config-plugin (e.g. Apple/Google sign-in). Regenerates the
# native project from app.json, signs with your Apple team, and launches.
# Set LANG/LC_ALL so CocoaPods (Ruby) doesn't choke on a non-UTF-8 locale.
mobile-ios:
	cd mobile && LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PATH="$(MOBILE_NODE_BIN):$$PATH" npx expo run:ios

# Typecheck the mobile app (matches the CI `mobile` job).
mobile-typecheck:
	cd mobile && PATH="$(MOBILE_NODE_BIN):$$PATH" npm run typecheck

# Lint the mobile app (matches the CI `mobile` job).
mobile-lint:
	cd mobile && PATH="$(MOBILE_NODE_BIN):$$PATH" npm run lint

# Install the mobile app's npm dependencies with the pinned Node.
mobile-install:
	cd mobile && PATH="$(MOBILE_NODE_BIN):$$PATH" npm install
