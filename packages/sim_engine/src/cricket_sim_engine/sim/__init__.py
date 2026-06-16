"""Application/state layer for the Cricket franchise sim's web UI.

This package is the bridge between `ui_server`'s HTTP handler and the domain
model in `models`/`engine`/`players_data`. Two classes do almost all the work:

- `LiveMatch` ([live_match](live_match.py)) drives a single match end-to-end —
  toss, lineups, over-by-over simulation (via `MatchEngine`), innings
  transitions, super overs, impact substitutions, and the live scorecard
  payload sent to the frontend.
- `LeagueState` ([league_state](league_state.py)) owns everything above a
  single match — the season schedule, standings, the mega draft,
  retention/regen between seasons, playoffs, and serialization (save/load) of
  the whole league to disk.

[helpers](helpers.py) holds small role/phase classification utilities shared
by both classes, and [constants](constants.py) holds shared seed data and
sizing/persistence constants.
"""
from cricket_sim_engine.sim.league_state import LeagueState
from cricket_sim_engine.sim.live_match import LiveMatch

__all__ = ["LeagueState", "LiveMatch"]
