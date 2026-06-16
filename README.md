# Cricket Franchise Sim

A cricket franchise career simulation. Pick a team, run the mega draft, play or sim every match over-by-over, manage retentions, and build a dynasty across multiple seasons.

Runs as a **React Native / Expo mobile app** (iOS/Android) backed by a **FastAPI + Postgres + Redis** service, with the original browser frontend kept for validation. Accounts are durable: play as a guest and link Sign in with Apple / Google to keep your career across devices.

## Features

### Franchise Management
- **Mega draft** — 10 teams, 25 players each, snake order, max 9 overseas per squad. Draft manually pick by pick, autodraft one pick at a time, or let the CPU run the whole thing.
- **Three starting modes** — current-era mega draft, all-time-greats mega draft (500+ historical T20 cricket legends with career-based ratings), or skip the draft entirely and start the season with each franchise's real-world cricket 2026 roster.
- **Three difficulty levels** — Easy, Medium, Hard (affects CPU squad quality and match engine).
- **Leadership** — assign captain, vice-captain, and preferred wicketkeeper.
- **Saved presets ("11+1" model)** — set a Starting XI and one Impact Sub, plus a default batting order and 20-over bowling plan, that auto-apply every match. The captain, vice-captain, and designated wicketkeeper are locked into the Starting XI and can't be subbed out.

### Season Structure
- **14-round league stage** — 5 matches per round across all 10 teams. The schedule guarantees every team plays each of the other 9 at least once, with 5 repeat fixtures, and no pair ever meets more than twice. Simulate any round instantly or play your match live.
- **Points table and NRR** — live standings updated after every result.
- **Modern playoff bracket** — top 4 qualify. Qualifier 1, Eliminator, Qualifier 2, Final. Play your matches or quick-sim any you're not in.
- **Season history** — champion, runner-up, season MVP, final standings, and top batting/bowling tables archived every season.

### Match Engine
- **Over-by-over interactive play** — play a full over, a single ball, or play until a wicket falls.
- **Toss** — if you win the toss, choose bat or bowl; otherwise the CPU decides.
- **Lineup selection** — pick your XI from your 25-player squad (max 4 overseas in the XI), set batting order, assign a bowler per over or use your saved plan.
- **Smart batting order** — XIs are auto-arranged by best fit per slot (factoring in each player's natural batting position and phase rating, with tail-enders seated last), grouped into Openers / Middle Order / Death Overs / Tail zones across the draft, squad, and lineup screens. The same smart order the squad screen shows is what a quick-sim plays and the match-hub lineup pre-fills — no need to save presets first.
- **Aggression sliders** — set per-batter and per-bowler aggression (1–5) live during the match.
- **Impact Player rule** — one substitution per innings, any time before the 15th over of the second innings. Swap in a specialist bowler when defending or an extra hitter when chasing.
- **Next-batter selection** — after a wicket, choose who comes in next.
- **Super Over** — tied matches go to a super over; pick 2 batters and 1 bowler.
- **Auto-finish** — hand any live match to the engine to complete it instantly.

### Stats and Leaderboards
Per player, per season: runs, balls, average, strike rate, highest score, 50s, 100s, fours, sixes, wickets, economy, bowling average, bowling SR, best figures, catches, stumpings, run-outs, MoTM awards, MVP score.

Leaderboards: Orange Cap, Purple Cap, sixes, fours, boundaries, highest score, strike rate, economy, best figures, fielding, MVP.

### Multi-season Career
- **Retention window** — alternates between a 11-player and 5-player keep limit. CPU teams retain their best players by MVP score; you choose yours.
- **Post-retention draft** — reverse-standings order (no snake), giving last-placed teams first pick of the released pool.
- **Player progression** — ratings, form, and age update each off-season. Young players develop; veterans decline.
- **Regen prospects** — ~30 young domestic/overseas players are generated and added to the pool before each new draft.
- **Save/load** — full career state (including in-progress matches) is saved to named slots under `saves/`.

### Onboarding
- **Guided spotlight tour** — a first-run walkthrough that drives the real app: it moves tab to tab, dims the screen, and spotlights the area each step describes (Home → Squad → Season → Match Centre → Stats → History). Replayable any time from the account menu's "How to Play".

### Legal
- **Hosted Terms of Service & Privacy Policy** — published via GitHub Pages from `docs/legal/`, and linked in-app from the sign-in screen and account sheet. These double as the public policy URLs required by the App Store / Play Store.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package manager)
- Node ≥ 20.19.4 (for the mobile app)

## Setup

The primary stack is the **Expo mobile app + FastAPI backend**. To run it locally:

```bash
make install                                                  # Python deps
make backend-up && make backend-migrate && make backend-run   # Postgres + Redis + API on :8000
make mobile-install && make mobile                            # Metro + dev client on :8081
```

The original browser frontend is kept for quick validation without the mobile toolchain:

```bash
make run   # legacy stdlib web server
```

Then open [http://localhost:8765](http://localhost:8765) in your browser.

## Other commands

```bash
make test          # run the test suite
make test ARGS="-k impact_sub"   # filter tests by name
make lint          # pyflakes static check
make kill          # stop any running legacy/ui_server.py process
make clean         # remove __pycache__ / .pyc files
```

## Data files

`players.csv` and `players_alltime.csv` live in the `cricket_sim_engine` package and contain the current-era and all-time player pools respectively, including each player's `natural_slot` (1-11) used to seed the smart batting order. Both are required to run the app.

## Project structure

This repo is a `uv` workspace with three parts:

```
packages/sim_engine/         — cricket_sim_engine: the core simulation engine (installable package)
  src/cricket_sim_engine/
    sim/
      league_state.py        — top-level state machine: draft, schedule, playoffs, retention, save/load
      live_match.py           — single-match driver: toss, lineups, over-by-over play, super over
      helpers.py              — role/phase classification utilities
      constants.py            — seed data, squad sizes, team branding
    engine.py                 — per-ball outcome sampler (batting/bowling matchup model)
    models.py                 — Player and Team data classes, progression logic
    players_data.py           — loads players.csv / players_alltime.csv into Player objects, T20 2026 rosters
    players.csv, players_alltime.csv

backend/                      — FastAPI service (Postgres + Redis) — see backend section below
  app/
    main.py                   — FastAPI app entrypoint
    db/                        — SQLAlchemy models, session
    auth/, careers/, live_match/, season/  — route modules
  alembic/                    — DB migrations
  docker-compose.yml          — local Postgres + Redis

mobile/                       — React Native / Expo app (the primary frontend)
  src/
    app/                       — expo-router screens (tabs: home, squad, season, stats, history)
    components/                — draft hub, live-match hub, squad/lineup editors, sign-in, account sheet
    context/                   — Auth, Career, League, Theme providers
    api/                       — typed client for the FastAPI backend (auth, careers, live match)

webapp/                       — original static browser frontend (index.html, app.js, styles.css)

legacy/                        — original stdlib HTTP server (ui_server.py), kept as a fallback
                                  until the FastAPI backend reaches feature parity

tests/                         — pytest suite for cricket_sim_engine (engine, league state, live match, models)
legacy/tests/                  — tests for the legacy ui_server.py
```

## Backend (FastAPI + Postgres + Redis)

```bash
make backend-up        # start Postgres + Redis (Docker)
make backend-migrate   # apply Alembic migrations
make backend-run       # start the FastAPI dev server at http://localhost:8000
make backend-down      # stop Postgres + Redis
```

Copy `backend/.env.example` to `backend/.env` to override defaults (DB URL, Redis URL, etc.).
For a real (non-default) JWT secret locally, run `make gen-secret` once — it writes a strong
`JWT_SECRET` to the gitignored `backend/.env.local`, which takes precedence over `.env`. See
[Deploying to production](#deploying-to-production) for how secrets work in production.

## Mobile app (React Native / Expo)

The app lives in `mobile/` and talks to the FastAPI backend. Expo/Metro needs Node ≥ 20.19.4; the `make mobile*` targets auto-select the newest installed nvm Node ≥ 20.

```bash
make backend-up && make backend-migrate && make backend-run   # backend first

make mobile-install    # install JS deps (first time)
make mobile            # start Metro + the dev client on :8081
make mobile-ios        # build + run the native iOS dev client on a simulator
make mobile-typecheck  # tsc --noEmit  (matches CI)
make mobile-lint       # expo lint    (matches CI)
```

If the iOS Simulator's dev client shows "Could not connect to development server",
run `make mobile-sim-open` to point it at `127.0.0.1:8081`.

**Native modules / sign-in.** Apple and Google sign-in are native modules, so they
only work in a development build (`make mobile-ios`), not a bare Metro reload.
After changing a config plugin or native dependency, re-run `make mobile-ios`.

- **Sign in with Apple** (iOS) needs a paid Apple Developer team to provision the
  capability; set it under the target's Signing & Capabilities in Xcode.
- **Google sign-in** needs OAuth client IDs (iOS + Web) from Google Cloud Console.
  Provide them via `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID` / `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`
  and the backend's `google_client_ids`. The Web client ID is the token audience the
  backend verifies, so the two must match. Never commit OAuth client *secrets*.

### Accounts & cloud save

- Play immediately as a **guest** — the career is saved server-side and survives
  sign-out and app reloads on the same device.
- **Link Apple or Google** from the account sheet to make the account durable and
  portable; the existing guest career carries over.
- Tokens: short-lived access token + 30-day rotating refresh token, stored in the
  device keychain (`expo-secure-store`).

## Deploying to production

The backend refuses to start in production with insecure defaults (it calls
`Settings.validate_production_safety()` at boot). Before deploying, set these on your
host (Railway / Render / Fly.io / a VPS — use the host's **secrets / environment
variables** panel; do **not** commit them):

| Variable | Production value |
| --- | --- |
| `ENVIRONMENT` | `production` (turns on the safety checks below) |
| `JWT_SECRET` | A strong, random secret (≥ 32 chars). Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. |
| `CORS_ALLOW_ORIGINS` | An explicit, comma-separated allowlist of web origins (not `*`). Only matters for browser callers — the native app sends no Origin. |
| `DATABASE_URL` / `REDIS_URL` | Your managed Postgres / Redis connection strings. |
| `SENTRY_DSN` | (optional) Your Sentry project DSN for crash reporting. |

**Legal pages.** The Terms of Service and Privacy Policy live in `docs/legal/`
(Markdown sources + publish-ready HTML) and are published via GitHub Pages (Pages
source = `/docs` on `main`), e.g.
`https://akshayraj18.github.io/cricket_sim/legal/terms.html`. The mobile app links to
those URLs by default; override per-build with `EXPO_PUBLIC_TERMS_URL` /
`EXPO_PUBLIC_PRIVACY_POLICY_URL` (e.g. a custom marketing domain). App Store / Play
Store submissions need both to resolve on a stable public URL.

**About the JWT secret.** It signs the login tokens — anyone who knows it can forge a
session for any user, so treat it like a master password.

- **Generate it once and keep it stable.** Changing it invalidates every existing
  session (all users get logged out). Only rotate deliberately.
- **Production:** set `JWT_SECRET` in your host's secrets panel. This is what most apps
  do — the secret lives in the deploy environment, never in the repo. No third-party
  secrets product (Vault/Doppler/etc.) is required at this scale; your host's built-in
  env panel is the standard answer.
- **Local / self-hosted convenience:** `make gen-secret` writes a stable secret to the
  gitignored `backend/.env.local` (and refuses to overwrite an existing one, so you
  can't accidentally rotate). Real OS environment variables still override it.

**Rate limiting** (`/auth/*`) is Redis-backed, so production needs a reachable Redis;
it fails open (allows requests) if Redis is down. This throttles credential/token abuse
but is **not** DDoS protection — put a CDN/WAF/reverse proxy (e.g. Cloudflare) in front
for network-layer protection.
