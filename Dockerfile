# Backend image for the Cricket Sim FastAPI service.
#
# This is a uv WORKSPACE: `backend` depends on the `cricket-sim-engine` package
# in `packages/sim_engine`, so the build context is the REPO ROOT (not backend/)
# and we sync the whole workspace. The engine's player CSVs ship inside its
# package, so they land in the image automatically.
#
# Migrations are NOT run at build time (the DB isn't reachable then) — the
# start script (start.sh) runs `alembic upgrade head` at boot, then launches
# uvicorn bound to Railway's $PORT.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# uv: copy the cache into the image layer and don't try to use hardlinks across
# the bind mount; compile bytecode for faster cold starts.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Install dependencies first (cached unless the lockfile/manifests change).
#    We need every workspace member's pyproject for `uv sync` to resolve the
#    `cricket-sim-engine = { workspace = true }` source.
COPY pyproject.toml uv.lock ./
COPY packages/sim_engine/pyproject.toml packages/sim_engine/pyproject.toml
COPY backend/pyproject.toml backend/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package cricket-sim-backend

# 2) Copy the source and install the workspace packages themselves.
COPY packages/sim_engine ./packages/sim_engine
COPY backend ./backend
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package cricket-sim-backend

# Run migrations + start the server from the backend dir (where alembic.ini lives).
WORKDIR /app/backend
COPY backend/start.sh /app/backend/start.sh
RUN chmod +x /app/backend/start.sh

# Railway injects $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000

CMD ["/app/backend/start.sh"]
