# Deploying the backend to Railway

The backend ships as a Docker image built from the repo root (it's a uv
workspace — the FastAPI app depends on the `cricket-sim-engine` package). The
image runs `alembic upgrade head` at boot, then launches uvicorn on `$PORT`.

Build + run are verified locally (`Dockerfile`, `backend/start.sh`,
`railway.json`). Follow the steps below to put it on Railway.

## 1. Create the Railway project

1. Sign in at https://railway.app with **Login with GitHub** (so it can read this repo).
2. **New Project → Deploy from GitHub repo → `akshayraj18/cricket_sim`**.
3. Railway detects `railway.json` and builds with the `Dockerfile`. (If it asks
   for a root directory, leave it as the repo root — the Dockerfile expects that.)

## 2. Add Postgres and Redis

In the same project:

1. **New → Database → Add PostgreSQL.**
2. **New → Database → Add Redis.**

Railway creates `DATABASE_URL` and `REDIS_URL` variables on those services.

## 3. Wire the database/redis URLs into the API service

On the **API service → Variables**, add references to the DB/Redis URLs (Railway
supports variable references with `${{ ... }}`):

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | `${{ Postgres.DATABASE_URL }}` |
| `REDIS_URL` | `${{ Redis.REDIS_URL }}` |

(The app rewrites a `postgres://` / `postgresql://` URL to `postgresql+asyncpg://`
automatically, so paste Railway's value as-is.)

## 4. Set the production secrets

On the **API service → Variables**, add:

| Variable | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `JWT_SECRET` | A strong random secret — generate once with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. **Keep it stable; changing it logs everyone out.** |
| `CORS_ALLOW_ORIGINS` | Explicit allowlist, comma-separated. The native app sends no Origin, so this only matters for browser callers. If only the app uses the API, set it to your own domain or a placeholder like `https://cricketfranchisesim.app` — **not** `*` (the app refuses to boot with `*` in production). |
| `SENTRY_DSN` | (optional) Your Sentry DSN for crash reporting. Leave unset to disable. |

> The backend calls `validate_production_safety()` at startup and **refuses to
> boot** if `ENVIRONMENT=production` with a dev/weak `JWT_SECRET` or `*` CORS.
> That's intentional — a failed deploy here means a secret isn't set.

## 5. Deploy + verify

1. Trigger a deploy (Railway auto-deploys on push to `main`, or click **Deploy**).
2. Watch the build/deploy logs — you should see:
   - `[start] Applying database migrations (alembic upgrade head)...`
   - `INFO: Application startup complete.`
3. Railway assigns a public URL. Under **Settings → Networking**, generate a
   domain if one isn't shown.
4. Confirm it's live:
   ```
   curl https://<your-app>.up.railway.app/health
   # -> {"status":"ok"}
   ```

## 6. Point the mobile app at it

In the EAS/production build, set:

```
EXPO_PUBLIC_API_URL=https://<your-app>.up.railway.app
```

(That's the only change needed for the app to talk to production — the legal
links already point at GitHub Pages independently.)

## Local sanity check (optional)

You can run the exact image locally against the dev Postgres/Redis:

```
docker build -t cricket-sim-backend .
docker run --rm -p 8099:8000 \
  -e ENVIRONMENT=production \
  -e JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" \
  -e CORS_ALLOW_ORIGINS="https://example.com" \
  -e DATABASE_URL="postgresql://cricket_sim:cricket_sim@host.docker.internal:5432/cricket_sim" \
  -e REDIS_URL="redis://host.docker.internal:6379/0" \
  cricket-sim-backend
curl http://127.0.0.1:8099/health
```

(Requires the dev DB/Redis up: `make backend-up`.)
