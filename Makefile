.PHONY: install test test-all test-exhaustive unit integration regression lint clean \
	backend-up backend-down backend-run backend-migrate backend-test gen-secret \
	webapp \
	mobile mobile-install mobile-typecheck mobile-lint mobile-ios mobile-sim-open \
	mobile-prebuild mobile-xcode-env

# Install/sync project + dev dependencies (pytest, pyflakes) via uv.
install:
	uv sync

# The everyday run: basic user-facing behaviour plus intermediate/edge cases,
# excluding the exhaustive `slow` tier. This is what you run while iterating.
# Use `make test ARGS="-k impact_sub"` to filter.
test:
	uv run pytest -m "not slow" $(ARGS)

# Everything, including the exhaustive `slow` tier (full Test matches, repeated
# whole-season sims). This is what CI runs on every PR, so nothing reaches main
# without it — run it locally too before pushing something risky.
test-all:
	uv run pytest $(ARGS)

# Just the exhaustive tier, for when you're specifically poking at it.
test-exhaustive:
	uv run pytest -m slow $(ARGS)

# Run only fast, isolated unit tests (helpers, models, engine, players_data).
unit:
	uv run pytest -m unit $(ARGS)

# Run only integration tests (draft/lineup/match-flow/league-state flows).
integration:
	uv run pytest -m integration $(ARGS)

# Run only regression tests (whole-career/season lifecycle).
regression:
	uv run pytest -m regression $(ARGS)

# Static-check for undefined names, unused imports, etc.
lint: check-legal
	uv run pyflakes packages/sim_engine/src/cricket_sim_engine tests backend/app backend/tests

# Regenerate docs/legal/*.html from the .md sources. GitHub Pages serves docs/
# from main as-is, so the .html has to be committed -- but it is generated, not
# edited. Edit the .md and run this.
legal:
	python3 tools/build_legal_html.py

# Fail if the committed .html does not match the .md. They used to be
# maintained by hand, and an edit that landed in only one of them published a
# privacy policy describing the wrong app.
check-legal:
	python3 tools/build_legal_html.py --check

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

# Start the FastAPI dev server at http://0.0.0.0:8000 (reachable by iOS Simulator via LAN IP)
backend-run:
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --reload --port 8000

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

# --- Browser web app (webapp/) -------------------------------------------------

# Serve the static browser UI against the local FastAPI backend.
# Run `make backend-run` first in another shell, then open http://localhost:8765.
webapp:
	uv run python3 -m http.server 8765 --directory webapp

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

# Regenerate the native iOS project from app.json and reinstall pods. Run this
# after ANY dependency or config-plugin change: `expo install` updates
# node_modules but leaves Podfile.lock pinned to the old version, and the build
# then fails on a header that only exists in the newer pod.
# Depends on mobile-xcode-env so the local build environment survives the
# regeneration (prebuild --clean deletes ios/, and ios/ is gitignored).
mobile-prebuild:
	cd mobile && LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PATH="$(MOBILE_NODE_BIN):$$PATH" \
		arch -arm64 npx expo prebuild --clean --platform ios
	$(MAKE) mobile-xcode-env

# Write ios/.xcode.env.local, which Xcode build phases source.
#
# Sentry's build phase uploads source maps unless told not to, and that needs an
# auth token we do not have (secrets/ids.txt holds ingest-only DSNs), so the
# build dies with "An organization ID or slug is required". eas.json sets this
# same flag for cloud builds, but a local Xcode build never reads eas.json.
# ios/ is gitignored and regenerated, so this has to be reapplied, not committed.
mobile-xcode-env:
	@mkdir -p mobile/ios
	@touch mobile/ios/.xcode.env.local
	@grep -q NODE_BINARY mobile/ios/.xcode.env.local || \
		echo 'export NODE_BINARY=$(MOBILE_NODE_BIN)/node' >> mobile/ios/.xcode.env.local
	@grep -q SENTRY_DISABLE_AUTO_UPLOAD mobile/ios/.xcode.env.local || \
		echo 'export SENTRY_DISABLE_AUTO_UPLOAD=true' >> mobile/ios/.xcode.env.local
	@echo "ios/.xcode.env.local ready:"; sed 's/^/  /' mobile/ios/.xcode.env.local

# Build + run the native iOS dev client on a simulator. Needed after adding a
# native module / config-plugin (e.g. Apple/Google sign-in). Regenerates the
# native project from app.json, signs with your Apple team, and launches.
# Set LANG/LC_ALL so CocoaPods (Ruby) doesn't choke on a non-UTF-8 locale.
mobile-ios: mobile-xcode-env
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
