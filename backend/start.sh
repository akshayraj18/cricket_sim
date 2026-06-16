#!/usr/bin/env bash
# Boot the backend: apply DB migrations, then launch the API server.
# Run from /app/backend (where alembic.ini lives). Railway sets $PORT.
set -euo pipefail

echo "[start] Applying database migrations (alembic upgrade head)..."
uv run --package cricket-sim-backend alembic upgrade head

echo "[start] Launching uvicorn on 0.0.0.0:${PORT:-8000}..."
exec uv run --package cricket-sim-backend uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
