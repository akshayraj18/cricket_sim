# CricSim

A cricket franchise and international career simulation. Draft players, manage your squad, play or simulate every match ball-by-ball, and build a dynasty across formats and seasons.

**Stack:** React Native / Expo (iOS/Android) · FastAPI + Postgres + Redis · Python sim engine

Live on the App Store. Backend deployed on Railway.

---

## What you can do

### Careers
- **Indian T20 League** — 10 city franchises, 14-round league, IPL-style playoffs (Q1/Eliminator/Q2/Final). Draft from current 2026 rosters or 500+ all-time T20 greats.
- **International Tournament** — 10 nations (or 10 world city franchises for All-Time drafts), 9-round round-robin, semis + final (T20/ODI) or straight final (Test).
- **Bilateral Series** — Pick a nation, pick an opponent, play a full best-of-1/3/5 series across any format. All matches always play out.

### Formats
- **T20** — 20 overs, powerplay (1-6), middle (7-15), death (16-20). Impact Sub rule (IPL only). Super Over for ties.
- **ODI** — 50 overs, powerplay (1-10), middle (11-40), slog (41-50). 10-over bowler cap.
- **Test** — 5 days, 3 sessions/day, 30 overs/session. Follow-on, declarations, draws. 2 innings per side.

### Draft
- **Mega draft** — 10 teams, 25 players each, snake order, max 9 overseas per squad.
- **Three pools** — Current 2026 rosters (no draft, straight to season), All-Time T20 Greats, All-Time ODI Greats, All-Time Test Greats.
- **World city franchises** — All-Time tournament drafts use fictional world-city teams (Mumbai Monsoons, Sydney Sharks, etc.) with unique colors.

### Match engine
- Play ball-by-ball, over-by-over, or hand off to the engine.
- Aggression sliders (1–5) for batters and bowlers, live during the match.
- Smart batting order pre-filled by natural slot. Next-batter selection after wickets.
- Bowler selection each over (or CPU auto-selects with fatigue/rotation logic).
- Test: skip session, skip 10 overs, declare innings. ODI: end innings. T20: end innings, super over.

### Season & history
- Live standings with NRR. Match log. Per-player seasonal and career stats.
- Orange Cap / Purple Cap / season MVP. Full season history archive.
- Multi-season retention (11-player or 5-player window, alternating). Post-retention draft.

---

## Setup

Requires Python 3.12+, [uv](https://github.com/astral-sh/uv), Node ≥ 20.19.4.

```bash
# Install Python deps
make install

# Start backend (Postgres + Redis + API on :8000)
make backend-up && make backend-migrate && make backend-run

# Start mobile dev server (Metro + dev client on :8081)
make mobile-install && make mobile
```

If the iOS Simulator dev client shows "Could not connect", run:
```bash
make mobile-sim-open
```

---

## Make targets

```bash
make backend-up        # start Postgres + Redis containers
make backend-down      # stop containers
make backend-migrate   # run Alembic migrations
make backend-run       # start FastAPI on :8000 (with --reload)

make mobile            # start Metro + dev client on :8081
make mobile-ios        # build + run the native iOS dev client on a simulator
make mobile-prebuild   # regenerate ios/ and reinstall pods — run after ANY
                       #   dependency or config-plugin change (see below)
make mobile-xcode-env  # rewrite ios/.xcode.env.local (see below)
make mobile-typecheck  # tsc --noEmit
make mobile-lint       # expo lint

make test              # everyday run: basic + edge cases (~75s)
make test-all          # adds the exhaustive `slow` tier — what CI runs (~95s)
make test-exhaustive   # only the slow tier
make test ARGS="-k live_match"  # filter tests
make lint              # pyflakes static check
make clean             # remove __pycache__ / .pyc
```

### Two iOS build gotchas

Both of these have cost real debugging time, and both recur:

**After any dependency change, run `make mobile-prebuild`.** `expo install`
updates `node_modules` but leaves `Podfile.lock` pinned to the old version, so
the build fails on a header that only exists in the newer pod (for example
`'RNSContainer.h' file not found` after react-native-screens moved 4.25 → 4.26).

**Open `ios/CricSim.xcworkspace`, never `ios/CricSim.xcodeproj`.** CocoaPods
dependencies are only wired into the workspace; the bare project reproduces the
same missing-header errors.

`make mobile-ios` and `make mobile-prebuild` both run `make mobile-xcode-env`
first, which writes `ios/.xcode.env.local` with `SENTRY_DISABLE_AUTO_UPLOAD=true`.
Sentry's build phase otherwise tries to upload source maps, which needs an auth
token we don't have, and fails the build with "An organization ID or slug is
required". `eas.json` sets the same flag for cloud builds, but a local Xcode
build never reads `eas.json` — and `ios/` is gitignored and regenerated, so the
file can't simply be committed.

---

## Project structure

```
packages/sim_engine/               — installable Python package (cricket_sim_engine)
  src/cricket_sim_engine/
    engine.py                      — per-ball outcome sampler (MatchEngine)
    models.py                      — Player, Team data classes + progression
    players_data.py                — loads CSV pools into Player objects
    international_data.py          — current international rosters per format
    players.csv                    — IPL current 2026 roster pool
    players_alltime.csv            — IPL all-time T20 pool (500+ players)
    players_alltime_t20_intl.csv   — International all-time T20 pool
    players_alltime_odi.csv        — International all-time ODI pool
    players_alltime_test.csv       — International all-time Test pool
    sim/
      league_state.py              — career state machine (draft, schedule, playoffs, bilateral, save/load)
      live_match.py                — single-match driver (toss, lineup, over-by-over, Test sessions)
      helpers.py                   — role/phase classification utilities
      constants.py                 — MATCH_FORMAT_CONFIG, team branding, squad limits

backend/                           — FastAPI service
  app/
    main.py                        — app entrypoint, router registration
    auth/                          — JWT auth, Apple/Google sign-in, refresh tokens
    careers/                       — career CRUD, new-career wizard dispatch
    live_match/                    — over-by-over match actions (play-ball, play-over, declare, etc.)
    season/                        — round simulation, standings, playoff actions
    db/                            — SQLAlchemy models, Alembic migrations, Redis helpers
  docker-compose.yml               — local Postgres + Redis

mobile/                            — React Native / Expo app
  src/
    app/                           — expo-router screens + tabs (home, squad, season, stats, history)
    components/                    — live-match-hub, draft-hub, retention-hub, player-profile, etc.
    api/                           — typed FastAPI client (auth, careers, live match, season)
    context/                       — Auth, Career, League, Theme, Error providers
    observability/                 — Sentry + PostHog; use-funnel-tracking.ts derives
                                     the gameplay funnel from league-payload transitions
    constants/theme.ts             — team colors (IPL, international, world franchises), spacing, typography
    utils/lineup.ts                — batting order zones, bowler scoring, XI validation

docs/                              — reference documents (see below)
legacy/                            — original stdlib browser server (kept for quick local validation)
webapp/                            — original browser frontend (NOT part of the mobile release)
tests/                             — pytest suite (engine, league state, live match, models)
tools/ip_safe_rename.py            — real -> fictional name mapping and the script that
                                     applies it. PLAYER_MAP is the audit record; run
                                     `--check` before any release that adds player data
```

Player and franchise names shipped in the app are deliberately fictional
("Vyrat Kuhli", "Chennai Cholas"). Country names are real — they aren't
protected marks. See `docs/LAUNCH_ROADMAP.md` §0.1.

---

## Key docs

| File | What it covers |
|---|---|
| `docs/engine.txt` | Ball-by-ball probability model, format configs, all tuning values |
| `docs/new_career_schema.txt` | Career wizard flow, API payload, team lists, valid combinations |
| `docs/architecture.txt` | System architecture, data flow, key design decisions |
| `docs/LAUNCH_ROADMAP.md` | App Store / Play Store launch checklist, including the IP-safe naming rules |
| `docs/ideas.txt` | Feature backlog, phase roadmap, and the measured user-data snapshot the priorities are derived from |
| `docs/RELEASE_PLAN.md` | Scope, pre-flight checklist and accepted risks for the current release |
| `docs/CSV_ROSTER_IO.md` | Design for CSV roster export/import (not yet implemented) |
| `backend/DEPLOY.md` | Production deployment guide |

---

## Backend (FastAPI + Postgres + Redis)

```bash
make backend-up        # Docker: start Postgres + Redis
make backend-migrate   # apply Alembic migrations to local DB
make backend-run       # uvicorn on :8000 with --reload
```

Copy `backend/.env.example` to `backend/.env` for local config. For a real JWT secret:
```bash
make gen-secret        # writes JWT_SECRET to backend/.env.local (gitignored)
```

Production env vars (set in Railway/Render secrets panel — never commit):

| Variable | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `JWT_SECRET` | strong random secret (≥32 chars) |
| `DATABASE_URL` | managed Postgres connection string |
| `REDIS_URL` | managed Redis connection string |
| `CORS_ALLOW_ORIGINS` | explicit web origins (not `*`) |
| `SENTRY_DSN` | (optional) Sentry DSN |

The backend refuses to start in production with insecure defaults.

---

## Mobile (React Native / Expo)

Expo/Metro requires Node ≥ 20.19.4. The `make mobile*` targets auto-select the newest nvm Node ≥ 20.

```bash
make mobile-install    # npm install (first time only)
make mobile            # Metro + dev client on :8081
make mobile-ios        # rebuild native iOS app (after config plugin or native dep changes)
```

**Apple/Google sign-in** only works in a development build (`make mobile-ios`), not plain Metro. After changing a config plugin or native dependency, re-run `make mobile-ios`.

**Production builds** go through EAS Build (`eas build`). The production profile injects `EXPO_PUBLIC_API_URL` pointing at the Railway backend.

---

## Accounts

- **Guest** — career created immediately, saved server-side, survives restarts.
- **Link Apple or Google** — makes the account durable and device-portable; existing career carries over.
- Tokens: short-lived access token + 30-day rotating refresh token, stored in device keychain (`expo-secure-store`).

---

## Deploying to production

See `backend/DEPLOY.md` for the full production deployment checklist. Key points:
- Backend live at Railway. DB and Redis managed add-ons.
- Legal pages (ToS + Privacy Policy) published via GitHub Pages from `docs/legal/`.
- EAS Build handles signed iOS/Android release binaries.
