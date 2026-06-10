# IPL Franchise Sim

A browser-based IPL franchise career simulation. Pick a team, run the mega draft, play or sim every match over-by-over, manage retentions, and build a dynasty across multiple seasons.

## Features

### Franchise Management
- **Mega draft** — 10 teams, 21 players each, snake order. Draft manually pick by pick, autodraft one pick at a time, or let the CPU run the whole thing.
- **Three starting modes** — current-era mega draft, all-time-greats mega draft (500+ historical IPL legends with career-based ratings), or skip the draft entirely and start the season with each franchise's real-world IPL 2026 roster.
- **Three difficulty levels** — Easy, Medium, Hard (affects CPU squad quality and match engine).
- **Leadership** — assign captain, vice-captain, and preferred wicketkeeper.
- **Saved presets** — set a default batting order, 20-over bowling plan, batting-first XI, bowling-first XI, and Impact Player swap pairs that auto-apply every match.

### Season Structure
- **14-round league stage** — 5 matches per round across all 10 teams. Simulate any round instantly or play your match live.
- **Points table and NRR** — live standings updated after every result.
- **IPL playoff bracket** — top 4 qualify. Qualifier 1, Eliminator, Qualifier 2, Final. Play your matches or quick-sim any you're not in.
- **Season history** — champion, runner-up, season MVP, final standings, and top batting/bowling tables archived every season.

### Match Engine
- **Over-by-over interactive play** — play a full over, a single ball, or play until a wicket falls.
- **Toss** — if you win the toss, choose bat or bowl; otherwise the CPU decides.
- **Lineup selection** — pick your XI from your 21-player squad (max 4 overseas), set batting order, assign a bowler per over or use your saved plan.
- **Smart batting order** — XIs are auto-arranged by best fit per slot (factoring in each player's natural batting position and phase rating, with tail-enders seated last), grouped into Openers / Middle Order / Death Overs / Tail zones across the draft, squad, and lineup screens.
- **Aggression sliders** — set per-batter and per-bowler aggression (1–5) live during the match.
- **Impact Player rule** — one substitution per innings, any time before the 15th over of the second innings. Swap in a specialist bowler when defending or an extra hitter when chasing.
- **Next-batter selection** — after a wicket, choose who comes in next.
- **Super Over** — tied matches go to a super over; pick 2 batters and 1 bowler.
- **Auto-finish** — hand any live match to the engine to complete it instantly.

### Stats and Leaderboards
Per player, per season: runs, balls, average, strike rate, highest score, 50s, 100s, fours, sixes, wickets, economy, bowling average, bowling SR, best figures, catches, stumpings, run-outs, MoTM awards, MVP score.

Leaderboards: Orange Cap, Purple Cap, sixes, fours, boundaries, highest score, strike rate, economy, best figures, fielding, MVP.

### Multi-season Career
- **Retention window** — alternates between a 6-player and 3-player keep limit (mirrors IPL's periodic mega-auction cycle). CPU teams retain their best players by MVP score; you choose yours.
- **Post-retention draft** — reverse-standings order (no snake), giving last-placed teams first pick of the released pool.
- **Player progression** — ratings, form, and age update each off-season. Young players develop; veterans decline.
- **Regen prospects** — ~30 young domestic/overseas players are generated and added to the pool before each new draft.
- **Save/load** — full career state (including in-progress matches) is saved to named slots under `saves/`.

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package manager)

## Setup

```bash
# Install dependencies
make install

# Start the server
make run
```

Then open [http://localhost:8765](http://localhost:8765) in your browser.

## Other commands

```bash
make test          # run the test suite
make test ARGS="-k impact_sub"   # filter tests by name
make lint          # pyflakes static check
make kill          # stop any running ui_server.py process
make clean         # remove __pycache__ / .pyc files
```

## Data files

`players.csv` and `players_alltime.csv` are provided with the repo and contain the current-era and all-time player pools respectively, including each player's `natural_slot` (1-11) used to seed the smart batting order. Both are required to run the app.

## Project structure

```
ui_server.py        — HTTP server, routes /api/* actions to LeagueState
sim/
  league_state.py   — top-level state machine: draft, schedule, playoffs, retention, save/load
  live_match.py     — single-match driver: toss, lineups, over-by-over play, super over
  helpers.py        — role/phase classification utilities
  constants.py      — seed data, squad sizes, team branding
engine.py           — per-ball outcome sampler (batting/bowling matchup model)
models.py           — Player and Team data classes, progression logic
players_data.py     — loads players.csv / players_alltime.csv into Player objects, IPL 2026 rosters
static/             — frontend (index.html, app.js, styles.css)
tests/              — pytest suite covering the engine, league state, live match, models, and UI server
```
