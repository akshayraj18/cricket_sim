# CricSim Mobile

React Native / Expo app. See root `README.md` for full setup and `make` targets.

## Quick start

```bash
# From repo root:
make backend-up && make backend-run   # backend on :8000
make mobile                           # Metro + dev client on :8081
make mobile-sim-open                  # if simulator shows "Could not connect"
```

## After changing a native module or config plugin

```bash
make mobile-ios   # rebuild native dev client (needed for sign-in, push notifications, etc.)
```

## Checks (run before pushing)

```bash
make mobile-typecheck   # tsc --noEmit
make mobile-lint        # expo lint
```

## Key files

- `src/components/live-match-hub.tsx` — full match control UI (toss, lineup, over hub, scorecard)
- `src/components/draft-hub.tsx` — pick-by-pick draft
- `src/app/new-career.tsx` — career creation wizard
- `src/app/(tabs)/season.tsx` — standings + schedule + playoff bracket
- `src/constants/theme.ts` — all team colors, spacing, typography
- `src/utils/lineup.ts` — batting order zones, XI validation, bowler scoring
- `src/api/` — typed FastAPI client (auth, careers, live match, season)
