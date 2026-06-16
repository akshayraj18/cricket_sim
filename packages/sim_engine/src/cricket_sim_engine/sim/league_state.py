"""Top-level career state machine: schedule, draft, playoffs, retention, persistence.

`LeagueState` owns everything that spans matches — the player pool and ten
franchises, the mega draft, the season schedule and standings, the live match
in progress (a `LiveMatch`), the playoff bracket, end-of-season retention and
regeneration, leaderboards/serialisation, and save/load to disk.
"""
import os
import pickle
import random

from cricket_sim_engine.models import Player, Team
from cricket_sim_engine.players_data import IPL_TEAMS_LIST, get_initial_player_pool, get_alltime_player_pool, get_2026_rosters_and_pool
from cricket_sim_engine.sim.constants import (
    SAVE_FILE,
    SAVES_DIR,
    SQUAD_SIZE,
    MAX_OVERSEAS_SQUAD,
    RETAIN_NORMAL,
    RETAIN_RESET,
    INDIAN_FIRST_NAMES,
    INDIAN_LAST_NAMES,
    OVERSEAS_FIRST_NAMES,
    OVERSEAS_LAST_NAMES,
    team_meta,
)
from cricket_sim_engine.sim.helpers import (
    batting_slot_player,
    bowling_slot_player,
    bowling_kind,
    counts_as_batter,
    counts_as_bowler,
    ensure_stat_fields,
    expanded_batting_archetype,
    expanded_bowling_phase,
    innings_phase,
    is_batting_role,
    is_bowling_role,
    is_wicketkeeper_option,
    ordinal,
    phase_fit_label,
)
from cricket_sim_engine.sim.live_match import LiveMatch


class LeagueState:
    """Top-level state for an entire Cricket franchise career: drives the game's overall flow.

    `phase` is the master state machine ("title" -> "draft" -> "season" ->
    "playoffs" -> "offseason" -> ...), and this class owns everything that
    spans matches: the player pool and ten franchises, the mega draft, the
    round-robin schedule and standings, the live match in progress
    (`live_match`), the playoff bracket, end-of-season retention/regen, and
    persistence (pickled to `SAVE_FILE`). `payload()` serialises the relevant
    slice of all this for whatever screen the frontend is currently showing.
    """

    def __init__(self):
        self.phase = "title"
        self.season_year = 2026
        self.completed_seasons = 0
        self.difficulty = "hard"
        self.user_team_name = ""
        self.player_pool = []
        self.teams = []
        self.draft_type = "mega"
        self.draft_order = []
        self.draft_round = 1
        self.draft_index = 0
        self.draft_started = False
        self.pick_num = 1
        self.draft_history = []
        self.round_num = 1
        self.schedule = []
        self.match_log = []
        self.fixture_results = []
        self.playoff_matches = []
        self.playoff_index = 0
        self.playoff_results = []
        self.pending_playoff_top_four = []
        self.season_history = []
        self.status_message = "Create a league or load your saved cricket universe."
        self.live_match = None
        self.retention_limit = RETAIN_NORMAL
        self.last_standings = []
        self.save_name = ""
        self.draft_pool_type = "current"

    @staticmethod
    def save_slug(name):
        """Turn a user-supplied save name into a filesystem-safe slug (lowercase, alnum/dash/underscore only)."""
        slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.strip().lower())
        slug = "-".join(filter(None, slug.split("-")))
        return slug

    @staticmethod
    def save_path(name):
        return os.path.join(SAVES_DIR, f"{LeagueState.save_slug(name)}.pkl")

    def save(self, name=None):
        """Pickle the entire league state (including any in-progress match) to a named slot under `SAVES_DIR`.

        Uses `name` if given, else the save's existing `save_name`, else a
        name derived from the user's franchise. Raises `ValueError` if no
        usable name can be determined or the resulting slug is empty.
        """
        chosen = (name or self.save_name or self.user_team_name or "career").strip()
        if not self.save_slug(chosen):
            raise ValueError("Enter a valid save name.")
        self.save_name = chosen
        os.makedirs(SAVES_DIR, exist_ok=True)
        with open(self.save_path(chosen), "wb") as handle:
            pickle.dump(self, handle)

    @classmethod
    def list_saves(cls):
        """List available save slots, newest first: each entry has `name`, `team`, `season`, and `updated_at` (file mtime)."""
        if not os.path.isdir(SAVES_DIR):
            return []
        entries = []
        for filename in os.listdir(SAVES_DIR):
            if not filename.endswith(".pkl"):
                continue
            full_path = os.path.join(SAVES_DIR, filename)
            try:
                with open(full_path, "rb") as handle:
                    state = pickle.load(handle)
                entries.append({
                    "name": getattr(state, "save_name", "") or filename[:-4],
                    "team": getattr(state, "user_team_name", ""),
                    "season": getattr(state, "season_year", ""),
                    "phase": getattr(state, "phase", ""),
                    "updated_at": os.path.getmtime(full_path),
                })
            except Exception:
                continue
        entries.sort(key=lambda e: e["updated_at"], reverse=True)
        return entries

    @classmethod
    def load(cls, name=None):
        """Load and return a previously saved `LeagueState` by name, migrated to the current schema.

        Falls back to the most recently updated save when `name` isn't
        given (and to the legacy single-file `SAVE_FILE` if that's all that
        exists, migrating it into the new saves folder). Raises `ValueError`
        if no matching save exists.
        """
        path = None
        if name:
            candidate = cls.save_path(name)
            if os.path.exists(candidate):
                path = candidate
            else:
                raise ValueError(f'No save named "{name}" exists.')
        else:
            saves = cls.list_saves()
            if saves:
                path = cls.save_path(saves[0]["name"])
            elif os.path.exists(SAVE_FILE):
                path = SAVE_FILE
            else:
                raise ValueError("No local UI save exists yet.")
        with open(path, "rb") as handle:
            state = pickle.load(handle)
        state.migrate()
        if path == SAVE_FILE and not state.save_name:
            state.save_name = state.user_team_name or "career"
            state.save()
        return state

    @classmethod
    def delete_save(cls, name):
        """Remove a named save slot from disk. Raises `ValueError` if it doesn't exist."""
        path = cls.save_path(name)
        if not os.path.exists(path):
            raise ValueError(f'No save named "{name}" exists.')
        os.remove(path)

    def to_dict(self):
        """Serialise this career to a JSON-safe dict for DB persistence (`careers.state_blob`).

        Excludes `live_match`: an in-progress match is not persisted here
        (see the live-match/Redis layer) and always loads back as `None`.
        Object references to `Team`/`Player` instances (the draft order,
        last standings, player pool, and team rosters) are serialised by
        name/dict and resolved back against `self.teams` on `from_dict`.
        """
        return {
            "phase": self.phase,
            "season_year": self.season_year,
            "completed_seasons": self.completed_seasons,
            "difficulty": self.difficulty,
            "user_team_name": self.user_team_name,
            "player_pool": [p.to_dict() for p in self.player_pool],
            "teams": [t.to_dict() for t in self.teams],
            "draft_type": self.draft_type,
            "draft_order_names": [t.name for t in self.draft_order],
            "draft_round": self.draft_round,
            "draft_index": self.draft_index,
            "draft_started": self.draft_started,
            "pick_num": self.pick_num,
            "draft_history": self.draft_history,
            "round_num": self.round_num,
            "schedule": [[list(pair) for pair in round_] for round_ in self.schedule],
            "match_log": self.match_log,
            "fixture_results": self.fixture_results,
            "playoff_matches": self.playoff_matches,
            "playoff_index": self.playoff_index,
            "playoff_results": self.playoff_results,
            "pending_playoff_top_four": self.pending_playoff_top_four,
            "season_history": self.season_history,
            "status_message": self.status_message,
            "retention_limit": self.retention_limit,
            "last_standings_names": [t.name for t in self.last_standings],
            "save_name": self.save_name,
            "draft_pool_type": self.draft_pool_type,
        }

    @classmethod
    def from_dict(cls, data):
        """Reconstruct a `LeagueState` from a dict produced by `to_dict()`.

        `live_match` always loads as `None` (see `to_dict`). Team-reference
        lists (`draft_order`, `last_standings`) are resolved by name against
        the rebuilt `self.teams`.
        """
        state = cls()
        state.phase = data["phase"]
        state.season_year = data["season_year"]
        state.completed_seasons = data["completed_seasons"]
        state.difficulty = data["difficulty"]
        state.user_team_name = data["user_team_name"]
        state.player_pool = [Player.from_dict(p) for p in data.get("player_pool", [])]
        state.teams = [Team.from_dict(t) for t in data.get("teams", [])]
        teams_by_name = {t.name: t for t in state.teams}
        state.draft_type = data.get("draft_type", "mega")
        state.draft_order = [teams_by_name[name] for name in data.get("draft_order_names", []) if name in teams_by_name]
        state.draft_round = data.get("draft_round", 1)
        state.draft_index = data.get("draft_index", 0)
        state.draft_started = data.get("draft_started", False)
        state.pick_num = data.get("pick_num", 1)
        state.draft_history = data.get("draft_history", [])
        state.round_num = data.get("round_num", 1)
        state.schedule = [[tuple(pair) for pair in round_] for round_ in data.get("schedule", [])]
        state.match_log = data.get("match_log", [])
        state.fixture_results = data.get("fixture_results", [])
        state.playoff_matches = data.get("playoff_matches", [])
        state.playoff_index = data.get("playoff_index", 0)
        state.playoff_results = data.get("playoff_results", [])
        state.pending_playoff_top_four = data.get("pending_playoff_top_four", [])
        state.season_history = data.get("season_history", [])
        state.status_message = data.get("status_message", "")
        state.retention_limit = data.get("retention_limit", RETAIN_NORMAL)
        state.last_standings = [teams_by_name[name] for name in data.get("last_standings_names", []) if name in teams_by_name]
        state.save_name = data.get("save_name", "")
        state.draft_pool_type = data.get("draft_pool_type", "current")
        state.live_match = None
        return state

    def migrate(self):
        """Backfill attributes that may be missing from an older save file.

        Lets saves created before a feature existed (e.g. `fixture_results`,
        `retention_limit`) load without `AttributeError`s, and re-syncs each
        saved player's static data (ratings, archetypes, profile fields) with
        the current `players.csv`/generation logic — so balance tweaks made
        between sessions apply retroactively to existing careers without
        discarding their season stats, form, or roster assignments.
        """
        self.fixture_results = getattr(self, "fixture_results", [])
        self.match_log = getattr(self, "match_log", [])
        self.playoff_results = getattr(self, "playoff_results", [])
        self.pending_playoff_top_four = getattr(self, "pending_playoff_top_four", [])
        self.draft_started = getattr(self, "draft_started", self.phase != "draft" or bool(self.draft_history))
        self.last_standings = getattr(self, "last_standings", [])
        self.retention_limit = getattr(self, "retention_limit", RETAIN_NORMAL)
        self.save_name = getattr(self, "save_name", "")
        self.draft_pool_type = getattr(self, "draft_pool_type", "current")
        self.difficulty = getattr(self, "difficulty", "hard")
        if self.difficulty not in ("easy", "medium", "hard"):
            self.difficulty = "hard"
        try:
            current_player_data = {p.name: p for p in get_initial_player_pool()}
        except Exception:
            current_player_data = {}
        if getattr(self, "live_match", None):
            if getattr(self.live_match, "engine", None):
                self.live_match.engine.difficulty = self.difficulty
                self.live_match.engine.user_team_name = self.user_team_name
            self.live_match.super_over = getattr(self.live_match, "super_over", None)
            self.live_match.impact_subs = getattr(self.live_match, "impact_subs", [])
            if getattr(self.live_match, "score", None):
                self.live_match.score.setdefault("active_bowler", None)
                self.live_match.score.setdefault("current_over_events", [])
                self.live_match.score.setdefault("pending_next_batter", False)
                self.live_match.score.setdefault("batting_aggression", {p.name: 3 for p in self.live_match.score.get("batting_order", [])})
                self.live_match.score.setdefault("bowling_aggression", {p.name: 2 for p in self.live_match.score.get("bowling_pool", [])})
        for team in getattr(self, "teams", []):
            team.saved_playing_xi_names = getattr(team, "saved_playing_xi_names", [])
            team.saved_starting_xi_names = getattr(team, "saved_starting_xi_names", [])
            team.saved_impact_sub_name = getattr(team, "saved_impact_sub_name", "")
            team.saved_wicketkeeper_name = getattr(team, "saved_wicketkeeper_name", "")
            team.saved_batting_order_names = getattr(team, "saved_batting_order_names", [])
            team.saved_bowling_over_names = getattr(team, "saved_bowling_over_names", [])
            for player in team.roster:
                ensure_stat_fields(player)
                current = current_player_data.get(player.name)
                if current:
                    player.batting_archetype = current.batting_archetype
                    player.bowling_phase = current.bowling_phase
                    player.bowling_type = current.bowling_type
                    player.strengths = current.strengths
                    player.weaknesses = current.weaknesses
                player.base_ovr = max(player.batting_ovr, player.bowling_ovr)
        for player in getattr(self, "player_pool", []):
            ensure_stat_fields(player)
            current = current_player_data.get(player.name)
            if current:
                player.batting_archetype = current.batting_archetype
                player.bowling_phase = current.bowling_phase
                player.bowling_type = current.bowling_type
                player.strengths = current.strengths
                player.weaknesses = current.weaknesses
            player.base_ovr = max(player.batting_ovr, player.bowling_ovr)
        known_names = {p.name for p in getattr(self, "player_pool", [])}
        for team in getattr(self, "teams", []):
            known_names.update(p.name for p in team.roster)
        for player in current_player_data.values():
            if player.name not in known_names:
                player.team_name = "Unassigned"
                ensure_stat_fields(player)
                self.player_pool.append(player)

    def new_league(self, user_team_name, difficulty="hard", draft_pool="current"):
        """Reset to a brand-new career: fresh player pool and ten empty franchises, the user assigned to `user_team_name`, and a shuffled mega-draft order ready to start.

        `draft_pool` can be "current" (2026 players only) or "alltime" (500+ all-time IPL greats).
        Raises `ValueError` if `user_team_name` isn't a real cricket franchise.
        """
        if user_team_name not in IPL_TEAMS_LIST:
            raise ValueError("Choose a valid cricket franchise.")
        self.__init__()
        self.season_year = 2026
        self.difficulty = difficulty if difficulty in ("easy", "medium", "hard") else "hard"
        self.draft_pool_type = draft_pool if draft_pool in ("current", "alltime") else "current"
        self.user_team_name = user_team_name
        self.player_pool = get_alltime_player_pool() if self.draft_pool_type == "alltime" else get_initial_player_pool()
        self.teams = [Team(name) for name in IPL_TEAMS_LIST]
        self.phase = "draft"
        self.draft_type = "mega"
        self.draft_order = list(self.teams)
        random.shuffle(self.draft_order)
        self.draft_started = False
        self.match_log = []
        self.fixture_results = []
        self.live_match = None
        user_pick = self.draft_order.index(self.user_team()) + 1
        self.status_message = f"{user_team_name} enter a blank-franchise mega draft on {self.difficulty.title()} mode. You draft {ordinal(user_pick)}. Start the draft when ready."

    def new_league_with_rosters(self, user_team_name, difficulty="hard"):
        """Reset to a brand-new career using real-world IPL 2026 squads, skipping the mega draft entirely.

        Every franchise starts with its actual 2026 roster (`IPL_2026_ROSTERS`);
        players from `players.csv` not on any 2026 roster become the
        free-agent pool carried into next season's post-retention draft. The
        season starts immediately. Raises `ValueError` if `user_team_name`
        isn't a real IPL franchise.
        """
        if user_team_name not in IPL_TEAMS_LIST:
            raise ValueError("Choose a valid cricket franchise.")
        self.__init__()
        self.season_year = 2026
        self.difficulty = difficulty if difficulty in ("easy", "medium", "hard") else "hard"
        self.draft_pool_type = "rosters2026"
        self.user_team_name = user_team_name
        rosters, leftover_pool = get_2026_rosters_and_pool()
        self.player_pool = leftover_pool
        self.teams = [Team(name) for name in IPL_TEAMS_LIST]
        for team in self.teams:
            team.roster = list(rosters.get(team.name, []))
            for player in team.roster:
                player.team_name = team.name
        self.draft_type = "mega"
        self.draft_order = list(self.teams)
        self.draft_started = True
        self.start_regular_season()
        self.status_message = f"{user_team_name} take charge of their 2026 squad. League stage is ready."

    def build_schedule(self):
        """Build a 14-round league-stage schedule for 10 teams.

        Guarantees:
        - every team plays exactly once per round (no byes), so each round is a
          perfect matching of all 10 teams and every team plays 14 games;
        - every pair of teams meets *at least once* — the first 9 rounds are a
          full single round-robin (the circle method) covering all 45 pairs;
        - the remaining 5 rounds add a second meeting for 25 of those pairs
          (5 of the round-robin rounds, replayed), so each team gets exactly
          5 repeat fixtures (9 + 5 = 14);
        - **no pair meets 3+ times** — the 5 replayed rounds are distinct
          round-robin rounds, so no pair is ever scheduled more than twice.

        The schedule is randomised by shuffling which teams occupy the circle
        positions and which 5 rounds are replayed, so seasons differ while the
        guarantees above always hold.
        """
        names = [t.name for t in self.teams]
        # The circle method needs an even number of teams; with 10 it produces
        # 9 rounds, each a perfect matching, covering all 45 pairs exactly once.
        assert len(names) % 2 == 0, "schedule builder assumes an even team count"
        random.shuffle(names)

        # Single round-robin via the circle method: fix one team, rotate the
        # rest. Round r pairs position 0 with the last, then folds inward.
        n = len(names)
        rotation = list(names)
        single_rr = []
        for _ in range(n - 1):
            pairs = [
                (rotation[i], rotation[n - 1 - i])
                for i in range(n // 2)
            ]
            single_rr.append(pairs)
            # Rotate all but the first team one step (standard circle method).
            rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

        # Pick 5 distinct round-robin rounds to replay for the second meetings.
        # Distinct rounds => no pair appears more than twice across the season.
        extra_rounds = random.sample(single_rr, 14 - (n - 1))

        schedule = single_rr + extra_rounds
        random.shuffle(schedule)
        return schedule

    def user_team(self):
        """The `Team` the human user controls."""
        return self.find_team(self.user_team_name)

    def find_team(self, name):
        """Look up a `Team` by exact name. Raises `StopIteration` if no team has that name."""
        return next(t for t in self.teams if t.name == name)

    def standings(self, reverse=True):
        """Teams ranked by points, then net run rate, then wins — the standard IPL points-table tiebreak order."""
        return sorted(self.teams, key=lambda t: (t.points, t.net_run_rate, t.wins), reverse=reverse)

    def current_draft_order(self):
        """The pick order for the current draft round — reversed on even rounds for a mega draft (snake order, so no team is permanently advantaged by always picking last)."""
        if self.draft_type == "mega" and self.draft_round % 2 == 0:
            return list(reversed(self.draft_order))
        return list(self.draft_order)

    def current_draft_team(self):
        """The team on the clock right now, or `None` if the draft isn't active."""
        if self.phase != "draft":
            return None
        return self.current_draft_order()[self.draft_index]

    def start_draft(self):
        """Open the draft room and let CPU teams pick up to (but not including) the user's first turn."""
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        self.draft_started = True
        self.status_message = "Mega draft live. Squads are 25 players."
        self.cpu_until_user()

    def roster_needs(self, team):
        """How many more players of each kind (`wk`, `bat`, `bowl`, `ar`, `fast`, `spin`) this team should target to reach a balanced 25-player squad, based on simple minimum-count targets."""
        return {
            "wk": max(0, 2 - sum(1 for p in team.roster if is_wicketkeeper_option(p))),
            "bat": max(0, 9 - sum(1 for p in team.roster if batting_slot_player(p))),
            "bowl": max(0, 9 - sum(1 for p in team.roster if bowling_slot_player(p))),
            "ar": max(0, 2 - sum(1 for p in team.roster if p.role == "All-Rounder")),
            "fast": max(0, 4 - sum(1 for p in team.roster if p.role == "Bowler (Fast)")),
            "spin": max(0, 3 - sum(1 for p in team.roster if p.role == "Bowler (Spin)")),
        }

    def draft_score(self, team, player):
        """Heuristic CPU draft-pick value of `player` for `team`: higher is more attractive.

        Blends overall rating and youth with role-fit bonuses scaled by
        `roster_needs` (e.g. a wicketkeeper is worth more to a team that
        still needs one), penalises over-stacking a role or overseas slots
        (steering away as it nears the squad overseas cap), and penalises picks that don't
        address any remaining need once roster spots are running out. A small
        random jitter keeps CPU drafts from being perfectly deterministic.
        """
        needs = self.roster_needs(team)
        picks_left = SQUAD_SIZE - len(team.roster)
        score = player.current_ovr * 10 + max(0, 30 - player.age) * 1.6
        role_counts = {
            "wk": sum(1 for p in team.roster if is_wicketkeeper_option(p)),
            "bat": sum(1 for p in team.roster if p.role == "Batsman"),
            "bowl": sum(1 for p in team.roster if bowling_slot_player(p)),
            "ar": sum(1 for p in team.roster if p.role == "All-Rounder"),
        }
        if is_wicketkeeper_option(player):
            score += 8 if needs["wk"] else 0
        if player.role == "All-Rounder":
            two_way_value = (player.current_batting + player.current_bowling) * 0.30
            elite_side = max(player.current_batting, player.current_bowling) * 0.22
            score += two_way_value + elite_side + needs["ar"] * 16
            score += min(needs["bat"], 1) * 7 + min(needs["bowl"], 1) * 7
            if role_counts["ar"] >= 4:
                score -= 25 + (role_counts["ar"] - 3) * 20
        elif is_batting_role(player):
            score += player.current_batting * 0.30 + needs["bat"] * 7
            if role_counts["bat"] >= 8:
                score -= 25
        elif is_bowling_role(player):
            score += player.current_bowling * 0.30 + needs["bowl"] * 7
            if role_counts["bowl"] >= 8:
                score -= 25
        if player.role == "Bowler (Fast)":
            score += needs["fast"] * 5
        if player.role == "Bowler (Spin)":
            score += needs["spin"] * 5
        overseas = sum(1 for p in team.roster if p.is_overseas)
        # Steer the CPU off overseas players as it nears the squad cap; the cap
        # itself is enforced hard in draft_player, so this is just preference.
        if player.is_overseas and overseas >= MAX_OVERSEAS_SQUAD - 2:
            score -= 70
        if player.is_overseas and overseas >= MAX_OVERSEAS_SQUAD:
            score -= 999
        if picks_left <= sum(needs.values()) and not self.player_matches_need(player, needs):
            score -= 65
        return score + random.uniform(-10, 10)

    def player_matches_need(self, player, needs):
        """Whether drafting `player` would address at least one of `team`'s outstanding roster needs."""
        return (
            (is_wicketkeeper_option(player) and needs["wk"]) or
            (player.role == "All-Rounder" and needs["ar"]) or
            (batting_slot_player(player) and needs["bat"]) or
            (bowling_slot_player(player) and needs["bowl"]) or
            (player.role == "Bowler (Fast)" and needs["fast"]) or
            (player.role == "Bowler (Spin)" and needs["spin"])
        )

    def _overseas_count(self, team):
        """Number of overseas players currently on `team`'s roster."""
        return sum(1 for p in team.roster if p.is_overseas)

    def cpu_pick(self, team):
        """Have the CPU draft its single best-scoring available player for `team` (see `draft_score`).

        Respects the hard squad overseas cap: once `team` is at the limit, only
        domestic players are eligible (the scoring already steers away from
        overseas, but this guarantees the cap is never exceeded).
        """
        pool = self.player_pool
        if self._overseas_count(team) >= MAX_OVERSEAS_SQUAD:
            domestic = [p for p in pool if not p.is_overseas]
            if domestic:
                pool = domestic
        candidates = sorted(pool, key=lambda p: self.draft_score(team, p), reverse=True)
        self.draft_player(team, candidates[0])

    def draft_player(self, team, player):
        """Move `player` from the pool onto `team`'s roster, log the pick, advance the draft clock (snaking the round when the order wraps), and start the season once every squad reaches `SQUAD_SIZE`."""
        self.player_pool.remove(player)
        team.roster.append(player)
        player.team_name = team.name
        self.draft_history.append({
            "season": self.season_year,
            "type": self.draft_type,
            "round": self.draft_round,
            "pick": self.pick_num,
            "team": team.name,
            "player": player.name,
            "ovr": player.current_ovr,
            "role": player.role,
        })
        self.pick_num += 1
        self.draft_index += 1
        if self.draft_index >= len(self.draft_order):
            self.draft_index = 0
            self.draft_round += 1
        if all(len(t.roster) >= SQUAD_SIZE for t in self.teams):
            self.start_regular_season()

    def capture_season_baselines(self):
        """Snapshot every player's overall/batting/bowling ratings at the start of a season, so end-of-season summaries can show how much they've grown or declined."""
        for player in self.all_players():
            player.season_start_ovr = player.current_ovr
            player.season_start_bat = player.current_batting
            player.season_start_bowl = player.current_bowling

    def cpu_until_user(self):
        """Auto-pick for every CPU team in turn until it's the user's turn to draft (or the draft ends)."""
        while self.phase == "draft":
            team = self.current_draft_team()
            if team.name == self.user_team_name:
                return
            self.cpu_pick(team)

    def user_pick(self, player_name):
        """Draft the named player to the user's team on their turn, then let CPU teams pick until it's the user's turn again.

        Raises `ValueError` if the draft isn't open or the player is no
        longer available.
        """
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        player = next((p for p in self.player_pool if p.name == player_name), None)
        if not player:
            raise ValueError("Player is no longer available.")
        team = self.current_draft_team()
        if player.is_overseas and self._overseas_count(team) >= MAX_OVERSEAS_SQUAD:
            raise ValueError(
                f"Squad already has {MAX_OVERSEAS_SQUAD} overseas players (the limit). "
                "Draft a domestic player."
            )
        self.draft_player(team, player)
        self.cpu_until_user()

    def autodraft_user_pick(self):
        """Let the CPU make the user's pick for them on their current turn (per the same `draft_score` heuristic), then continue to the next user turn."""
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        team = self.current_draft_team()
        if team.name != self.user_team_name:
            self.cpu_until_user()
            team = self.current_draft_team()
        self.cpu_pick(team)
        self.cpu_until_user()

    def autodraft_to_end(self):
        """Run the entire remaining draft on autopilot, including the user's picks, until every squad is full and the season starts."""
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        while self.phase == "draft":
            self.cpu_pick(self.current_draft_team())

    def start_regular_season(self):
        """Transition from the draft to the league stage: build the schedule, reset match/playoff history, ensure every team has leadership assigned, and snapshot season-start ratings."""
        self.phase = "season"
        self.round_num = 1
        self.schedule = self.build_schedule()
        self.live_match = None
        self.match_log = []
        self.fixture_results = []
        self.playoff_matches = []
        self.playoff_results = []
        self.playoff_index = 0
        self.pending_playoff_top_four = []
        for team in self.teams:
            if not team.captain or team.captain not in team.roster:
                team.auto_assign_cpu_leadership()
        self.capture_season_baselines()
        self.status_message = f"Season {self.season_year} league stage is ready."

    def set_leadership(self, captain_name, vice_name, wicketkeeper_name=""):
        """Assign the user's captain, vice-captain, and (optionally) preferred wicketkeeper from their squad.

        Raises `ValueError` if the named captain/vice can't be resolved to
        two distinct squad members, the named keeper isn't an eligible
        wicketkeeper option, or any of the three isn't in the saved Starting
        XI (the captain, vice-captain, and designated wicketkeeper must
        always be in the Starting XI).
        """
        team = self.user_team()
        captain = next((p for p in team.roster if p.name == captain_name), None)
        vice = next((p for p in team.roster if p.name == vice_name), None)
        if not captain or not vice or captain == vice:
            raise ValueError("Choose two different players from your squad.")
        starting_xi = list(getattr(team, "saved_starting_xi_names", []))
        if starting_xi:
            if captain.name not in starting_xi:
                raise ValueError("Captain must be in the Starting XI.")
            if vice.name not in starting_xi:
                raise ValueError("Vice-captain must be in the Starting XI.")
            if wicketkeeper_name and wicketkeeper_name not in starting_xi:
                raise ValueError("Wicketkeeper must be in the Starting XI.")
        team.captain = captain
        team.vice_captain = vice
        if wicketkeeper_name:
            keeper = next((p for p in team.roster if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None)
            if not keeper:
                raise ValueError("Choose an eligible wicketkeeper from your squad.")
            team.saved_wicketkeeper_name = keeper.name

    def _reassign_leadership_for_xi(self, team, players):
        """Auto-reassign captain/vice-captain/wicketkeeper to fit a new Starting XI (`players`).

        Called whenever the saved Starting XI changes and the current
        captain, vice-captain, or designated keeper falls outside it (every
        leader must always be in the Starting XI). The new keeper is the
        highest-`current_ovr` wicketkeeper-eligible player in `players`; the
        new captain is the highest-`current_ovr` player in `players`; the new
        vice-captain is the next-highest. Falls back to leaving
        captain/vice-captain unset if `players` has no wicketkeeper option
        (the caller validates that case separately).
        """
        names_in_xi = {p.name for p in players}
        keeper_options = sorted([p for p in players if is_wicketkeeper_option(p)], key=lambda p: p.current_ovr, reverse=True)
        if (not team.captain or team.captain.name not in names_in_xi
                or not team.vice_captain or team.vice_captain.name not in names_in_xi
                or getattr(team, "saved_wicketkeeper_name", "") not in names_in_xi):
            if keeper_options:
                team.saved_wicketkeeper_name = keeper_options[0].name
            ranked = sorted(players, key=lambda p: p.current_ovr, reverse=True)
            team.captain = ranked[0]
            team.vice_captain = ranked[1]

    def set_user_presets(self, batting_order, bowling_order, starting_xi=None, impact_sub_name=None, wicketkeeper_name=""):
        """Save the user's reusable match-day defaults under the "11+1" model: a Starting XI, a single Impact Sub, a default batting order, a default 20-over bowling plan, and a preferred keeper.

        Validates XI composition (11 unique squad members, overseas limit, at
        least 6 batting options, at least one wicketkeeper-eligible player)
        and that the Impact Sub is a roster player not already in the
        Starting XI. The captain, vice-captain, and designated wicketkeeper
        must always be in the Starting XI; if the new Starting XI doesn't
        contain all three, leadership is auto-reassigned (see
        `_reassign_leadership_for_xi`) rather than rejecting the change.
        Raises `ValueError` on any invalid combination. A falsy
        `starting_xi`/`impact_sub_name` (`None`, `[]`, `""`) clears the
        corresponding saved preset, reverting to the smart default computed
        elsewhere (e.g. `team_dict`, `resolve_match_xi`).
        """
        team = self.user_team()
        roster_names = {p.name for p in team.roster}
        if starting_xi:
            clean_xi = [name for name in starting_xi if name in roster_names]
            if clean_xi:
                if len(clean_xi) != 11 or len(set(clean_xi)) != 11:
                    raise ValueError("Starting XI must contain 11 unique squad players.")
                players = [next(p for p in team.roster if p.name == name) for name in clean_xi]
                if sum(1 for p in players if p.is_overseas) > 4:
                    raise ValueError("Starting XI cannot include more than 4 overseas players.")
                if len([p for p in players if counts_as_batter(p)]) < 6:
                    raise ValueError("Starting XI needs at least 6 batting options including all-rounders and wicketkeepers.")
                if not any(is_wicketkeeper_option(p) for p in players):
                    raise ValueError("Starting XI needs at least one wicketkeeper.")
                team.saved_starting_xi_names = clean_xi
                self._reassign_leadership_for_xi(team, players)
        else:
            team.saved_starting_xi_names = []
        if impact_sub_name:
            if impact_sub_name not in roster_names:
                raise ValueError("Choose an Impact Sub from your squad.")
            current_xi = list(getattr(team, "saved_starting_xi_names", []))
            if impact_sub_name in current_xi:
                raise ValueError("Impact Sub must not already be in the Starting XI.")
            if impact_sub_name in (team.captain.name if team.captain else "", team.vice_captain.name if team.vice_captain else "", getattr(team, "saved_wicketkeeper_name", "")):
                raise ValueError("Impact Sub cannot be the captain, vice-captain, or wicketkeeper.")
            team.saved_impact_sub_name = impact_sub_name
        else:
            team.saved_impact_sub_name = ""
        if wicketkeeper_name:
            keeper = next((p for p in team.roster if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None)
            if not keeper:
                raise ValueError("Choose an eligible wicketkeeper from your squad.")
            team.saved_wicketkeeper_name = wicketkeeper_name
        batting = [name for name in batting_order if name in roster_names]
        if batting and (len(batting) != 11 or len(set(batting)) != 11):
            raise ValueError("Default batting order must contain 11 unique squad players.")
        bowlers = {p.name for p in team.roster if is_bowling_role(p)}
        bowling = [name for name in bowling_order if name in bowlers]
        if bowling and len(bowling) != 20:
            raise ValueError("Default bowling plan must contain 20 overs, or leave it blank.")
        if bowling and any(bowling.count(name) > 4 for name in set(bowling)):
            raise ValueError("No bowler can bowl more than 4 overs.")
        if bowling and any(bowling[i] == bowling[i - 1] for i in range(1, len(bowling))):
            raise ValueError("A bowler cannot bowl consecutive overs.")
        team.saved_batting_order_names = batting or list(getattr(team, "saved_starting_xi_names", []))
        team.saved_bowling_over_names = bowling

    def default_bowling_plan(self, team):
        """Build a 20-over bowling plan for `team`: the user's saved plan if they have one, otherwise auto-build one from their match-day 12 (Starting XI plus Impact Sub) by greedily picking the best phase-fit bowler for each over (never the same bowler in consecutive overs, never more than 4 overs each).

        Returns an empty list if the team can't field at least 5 recognised
        bowlers — the UI then falls back to choosing a bowler each over live.
        """
        saved = list(getattr(team, "saved_bowling_over_names", []))
        if saved:
            return saved
        starting_xi_names = list(getattr(team, "saved_starting_xi_names", [])) or self.smart_starting_xi(team)
        impact_sub_name = getattr(team, "saved_impact_sub_name", "") or self.smart_impact_sub(team, starting_xi_names)
        match_day_names = list(starting_xi_names) + ([impact_sub_name] if impact_sub_name else [])
        match_day = [next((p for p in team.roster if p.name == name), None) for name in match_day_names]
        match_day = [p for p in match_day if p]
        bowlers = sorted([p for p in match_day if is_bowling_role(p)], key=lambda p: p.current_bowling, reverse=True)
        if not bowlers:
            bowlers = sorted(team.roster, key=lambda p: p.current_bowling, reverse=True)[:5]
        if len(bowlers) < 5:
            return []
        def best_for_phase(phase, used, last_name):
            candidates = [p for p in bowlers if used.get(p.name, 0) < 4]
            non_repeat = [p for p in candidates if p.name != last_name]
            if non_repeat:
                candidates = non_repeat
            return sorted(candidates, key=lambda p: self.bowler_phase_score(p, phase), reverse=True)[0]
        used = {}
        plan = []
        for over in range(20):
            phase = innings_phase(over)
            bowler = best_for_phase(phase, used, plan[-1] if plan else "")
            plan.append(bowler.name)
            used[bowler.name] = used.get(bowler.name, 0) + 1
        # With exactly 5 bowlers x 4 overs, the greedy pass can paint itself
        # into a corner where the only bowler with quota left just bowled.
        # Repair any consecutive-over violations by swapping with another
        # over assigned to a different bowler, picking a swap that doesn't
        # create a new violation.
        for i in range(1, len(plan)):
            if plan[i] != plan[i - 1]:
                continue
            for j in range(len(plan)):
                if plan[j] == plan[i]:
                    continue
                prev_ok = j == 0 or plan[j - 1] != plan[i]
                next_ok = j == len(plan) - 1 or plan[j + 1] != plan[i]
                swap_prev_ok = i == 0 or plan[i - 1] != plan[j]
                swap_next_ok = i == len(plan) - 1 or plan[i + 1] != plan[j]
                if prev_ok and next_ok and swap_prev_ok and swap_next_ok:
                    plan[i], plan[j] = plan[j], plan[i]
                    break
        return plan

    def default_batting_order(self, team):
        """A sensible default batting order (player names) for `team`'s Starting XI: the user's saved order if usable, else freshly computed via `smart_batting_order`. Returns an empty list if the squad has fewer than 11 players."""
        if len(team.roster) < 11:
            return []
        xi_names = getattr(team, "saved_starting_xi_names", []) or self.smart_starting_xi(team)
        xi = [next((p for p in team.roster if p.name == name), None) for name in xi_names]
        xi = [p for p in xi if p]
        return [p.name for p in self.smart_batting_order(xi)]

    def bowler_phase_score(self, player, phase):
        """League-level heuristic for how well-suited this bowler is to the given match phase — used when auto-building bowling plans and CPU XIs (a slightly different weighting than `LiveMatch.bowler_phase_score`, which ranks live in-match options)."""
        score = player.current_bowling
        kind = bowling_kind(player)
        bowling_phase = getattr(player, "bowling_phase", "Flexible")
        bowling_type = getattr(player, "bowling_type", "")
        if bowling_phase == phase:
            score += 9
        if phase in ("Powerplay", "Death Overs") and kind == "pace":
            score += 5
        if phase == "Middle Overs" and kind == "spin":
            score += 7
        if phase == "Death Overs" and "Variations" in bowling_type:
            score += 5
        if "Mystery" in bowling_phase or "Mystery" in bowling_type:
            score += 2
        return score

    def batting_phase_score(self, player, phase):
        """Heuristic for how well this batter's archetype fits the given match phase, used to slot players into a sensible batting order (`smart_batting_order`)."""
        score = player.current_batting
        archetype = getattr(player, "batting_archetype", "")
        if phase == "Powerplay" and archetype in ("Aggressive Opener", "Aggressor", "Pace Specialist"):
            score += 10
        elif phase == "Powerplay" and archetype == "Anchor":
            score += 5
        elif phase == "Middle Overs" and archetype in ("Middle-over Rotator", "Strike Rotator", "Spin Specialist"):
            score += 9
        elif phase == "Death Overs" and archetype in ("Finisher", "Lower-order Hitter"):
            score += 11
        elif archetype == "Defensive Tailender":
            score -= 18
        if phase.lower().split()[0] in getattr(player, "strengths", "").lower():
            score += 3
        return score

    def smart_batting_order(self, players):
        """Arrange `players` (an XI) into a 1-11 batting order, honouring each player's natural batting slot.

        Every player carries a `preferred_position` (their `natural_slot` from
        the player CSV, where 1-2 are openers, 3-5 the middle order, 6-7 the
        death/finisher slots and 8-11 the tail). The order is a strict
        natural-slot assignment: players are sorted by `preferred_position`
        first, so a recognised batter never sits behind a tail-end bowler.
        Ties within the same natural slot are broken by current batting
        rating (the better batter goes first), with a tiny phase-fit nudge so
        two equally-rated, equally-slotted players settle in a sensible order.
        """
        remaining = list(dict.fromkeys(players))

        def natural(player):
            return getattr(player, "preferred_position", 6)

        def slot_phase(slot):
            if slot <= 2:
                return "Powerplay"
            if slot <= 5:
                return "Middle Overs"
            return "Death Overs"

        # Primary key: natural slot (CSV `natural_slot`). Secondary: a player
        # who bats better goes ahead of one with the same natural slot. The
        # phase-fit term is a small final tiebreak only.
        ordered = sorted(
            remaining,
            key=lambda p: (
                natural(p),
                -p.current_batting,
                -self.batting_phase_score(p, slot_phase(natural(p))),
            ),
        )
        return ordered[:11]

    def _ensure_natural_top_order_cover(self, selected, roster):
        """Swap in a bench batter if `selected` lacks anyone who naturally opens (preferred_position 1-2).

        A pure-rating XI pick can accidentally collect six middle-order/finisher
        types and nobody suited to actually face the new ball — this nudges in
        the best available natural opener at the expense of the weakest-fit
        specialist batter already picked, keeping the XI realistic.
        """
        def natural(p):
            return getattr(p, "preferred_position", 6)
        if any(counts_as_batter(p) and natural(p) <= 2 for p in selected):
            return
        bench_top_order = sorted(
            [p for p in roster if p not in selected and counts_as_batter(p) and natural(p) <= 2],
            key=lambda p: p.current_batting, reverse=True,
        )
        if not bench_top_order:
            return
        candidates = sorted([p for p in selected if counts_as_batter(p)], key=lambda p: (-natural(p), p.current_batting))
        if candidates:
            selected[selected.index(candidates[0])] = bench_top_order[0]

    def smart_cpu_xi(self, team):
        """Auto-pick a balanced playing XI for a CPU-controlled `team`.

        Always includes the captain/vice-captain and the best-batting
        wicketkeeper, then fills out to 6 specialist-ish batters and 5
        bowlers ranked by combined across-phase fit scores, topping up with
        the highest-rated remaining names — finally passed through
        `enforce_role_balance` to guarantee the minimums are actually met.
        """
        roster = list(team.roster)
        selected = []

        def add(player):
            if player and player not in selected and len(selected) < 11:
                selected.append(player)

        for leader in (team.captain, team.vice_captain):
            if leader in roster:
                add(leader)

        keepers = sorted([p for p in roster if is_wicketkeeper_option(p)], key=lambda p: (p.current_batting, p.current_ovr), reverse=True)
        add(keepers[0] if keepers else None)

        batters = sorted([p for p in roster if p not in selected and counts_as_batter(p)], key=lambda p: (
            self.batting_phase_score(p, "Powerplay") + self.batting_phase_score(p, "Middle Overs") + self.batting_phase_score(p, "Death Overs"),
            p.current_batting,
            p.current_ovr,
        ), reverse=True)
        for player in batters:
            if len([p for p in selected if counts_as_batter(p)]) >= 6:
                break
            add(player)
        self._ensure_natural_top_order_cover(selected, roster)

        bowlers = sorted([p for p in roster if p not in selected and counts_as_bowler(p)], key=lambda p: (
            self.bowler_phase_score(p, "Powerplay") + self.bowler_phase_score(p, "Middle Overs") + self.bowler_phase_score(p, "Death Overs"),
            p.current_bowling,
            p.current_ovr,
        ), reverse=True)
        for player in bowlers:
            if len([p for p in selected if counts_as_bowler(p)]) >= 5:
                break
            add(player)

        remaining = sorted([p for p in roster if p not in selected], key=lambda p: p.current_ovr, reverse=True)
        for player in remaining:
            add(player)

        return self.enforce_role_balance(selected, roster, min_batters=6, min_bowlers=5)

    def smart_starting_xi(self, team):
        """Auto-pick a batting-friendly Starting XI for `team`: best-batting keeper first, then up to 7 batting options ranked by combined phase fit, then the best death-overs bowlers to round out to 11 — passed through `enforce_role_balance`. Returns a list of player names."""
        roster = list(team.roster)
        selected = []
        keepers = sorted([p for p in roster if is_wicketkeeper_option(p)], key=lambda p: p.current_batting, reverse=True)
        if keepers:
            selected.append(keepers[0])
        bat_pool = sorted([p for p in roster if p not in selected], key=lambda p: self.batting_phase_score(p, "Powerplay") + self.batting_phase_score(p, "Middle Overs") + self.batting_phase_score(p, "Death Overs"), reverse=True)
        for p in bat_pool:
            if len([x for x in selected if is_batting_role(x)]) >= 7:
                break
            selected.append(p)
        bowl_pool = sorted([p for p in roster if p not in selected and is_bowling_role(p)], key=lambda p: self.bowler_phase_score(p, "Death Overs") + p.current_bowling, reverse=True)
        selected.extend(bowl_pool[:11 - len(selected)])
        selected.extend([p for p in roster if p not in selected][:11 - len(selected)])
        return [p.name for p in self.enforce_role_balance(selected, roster, min_batters=6, min_bowlers=4)]

    def complete_starting_xi(self, team, saved_names):
        """Reconcile a saved Starting XI with the current roster, preserving the
        user's choices as much as possible.

        Keeps the saved names that are still on the roster (in their saved
        order) and fills only the *missing* slots from the smart default XI, so
        a roster change (retention/draft/release dropping a player or two) no
        longer discards the entire saved XI and reverts to autofill. Returns
        exactly 11 names when the roster can field 11, else the best available.
        """
        roster_names = {p.name for p in team.roster}
        kept = [n for n in saved_names if n in roster_names]
        # De-dupe while preserving order (a corrupt save could repeat a name).
        seen = set()
        kept = [n for n in kept if not (n in seen or seen.add(n))]
        if len(kept) >= 11:
            return kept[:11]
        # Fill the gaps from the smart default, skipping anyone already kept.
        for name in self.smart_starting_xi(team):
            if len(kept) >= 11:
                break
            if name not in kept:
                kept.append(name)
        return kept[:11]

    def smart_impact_sub(self, team, starting_xi_names):
        """Pick the default Impact Sub for `team`: the best bowling-role player on the roster who isn't in `starting_xi_names` (the "12th player"), ranked by bowling rating. Falls back to the best-rated remaining player if the squad has no spare bowling option. Returns a player name, or "" if every roster player is already in the Starting XI."""
        bench = [p for p in team.roster if p.name not in starting_xi_names]
        if not bench:
            return ""
        bowlers = sorted([p for p in bench if counts_as_bowler(p)], key=lambda p: p.current_bowling, reverse=True)
        if bowlers:
            return bowlers[0].name
        return sorted(bench, key=lambda p: p.current_ovr, reverse=True)[0].name

    def resolve_match_xi(self, team, batting_first):
        """Derive `team`'s innings-1 XI and the Impact Sub swap pairing under the "11+1" model.

        `starting_xi` defaults to `smart_starting_xi(team)` and `impact_sub`
        defaults to `smart_impact_sub(team, starting_xi)`, falling back to the
        smart default if a saved choice is missing, no longer on the roster,
        or already in the Starting XI.

        `swap_out`/`swap_in` describe the pairing applied AT THE INNINGS BREAK:
        - Batting first: the Starting XI plays innings 1 unchanged; at the
          break, the weakest-bowling Starting XI player (`swap_out`) makes way
          for the Impact Sub (`swap_in`).
        - Bowling first: the Impact Sub already starts in place of that same
          player for innings 1 (so the bowling-heavy XI plays first); at the
          break, the Impact Sub (`swap_out`) makes way for the original player
          (`swap_in`), who returns.

        Returns `(innings1_xi_names, swap_out_name, swap_in_name)`. The
        4-overseas cap is respected when choosing `swap_out`.
        """
        roster_names = {p.name for p in team.roster}

        def overseas_ok(xi_names, out_name, in_name):
            xi_players = [p for p in team.roster if p.name in xi_names]
            out_player = next((p for p in team.roster if p.name == out_name), None)
            in_player = next((p for p in team.roster if p.name == in_name), None)
            overseas = sum(1 for p in xi_players if p.is_overseas)
            return overseas - int(out_player.is_overseas if out_player else False) + int(in_player.is_overseas if in_player else False) <= 4

        saved_xi = list(getattr(team, "saved_starting_xi_names", []))
        starting_xi = [name for name in saved_xi if name in roster_names]
        if len(starting_xi) != 11 or len(set(starting_xi)) != 11:
            # Preserve the still-valid saved picks and fill only the gaps,
            # rather than discarding the whole XI when the roster changes.
            starting_xi = self.complete_starting_xi(team, saved_xi) if saved_xi else self.smart_starting_xi(team)

        impact_sub = getattr(team, "saved_impact_sub_name", "")
        if impact_sub not in roster_names or impact_sub in starting_xi:
            impact_sub = self.smart_impact_sub(team, starting_xi)

        leaders = {team.captain.name if team.captain else "", team.vice_captain.name if team.vice_captain else "", getattr(team, "saved_wicketkeeper_name", "")}
        candidates = sorted(
            [p for p in team.roster if p.name in starting_xi and p.name not in leaders],
            key=lambda p: p.current_bowling,
        )
        if not candidates:
            candidates = sorted([p for p in team.roster if p.name in starting_xi], key=lambda p: p.current_bowling)
        swap_out = next((p.name for p in candidates if overseas_ok(starting_xi, p.name, impact_sub)), candidates[0].name if candidates else "")

        if batting_first:
            return starting_xi, swap_out, impact_sub
        innings1_xi = [impact_sub if name == swap_out else name for name in starting_xi]
        return innings1_xi, impact_sub, swap_out

    def enforce_xi_limits(self, selected, roster):
        """Trim `selected` to 11 and swap out the lowest-rated overseas players for the best available domestic ones until the squad respects the 4-overseas-player limit.

        Prefers a domestic replacement that matches the removed player's
        batting/bowling role-counting (`counts_as_batter`/`counts_as_bowler`),
        so this swap doesn't undo a role balance already established by
        `enforce_role_balance` — falling back to the best-OVR domestic option
        if no same-role replacement is available.
        """
        selected = selected[:11]
        while sum(1 for p in selected if p.is_overseas) > 4:
            overseas = [p for p in selected if p.is_overseas]
            remove = sorted(overseas, key=lambda p: p.current_ovr)[0]
            selected.remove(remove)
            domestic_pool = sorted([p for p in roster if not p.is_overseas and p not in selected], key=lambda p: p.current_ovr, reverse=True)
            domestic = next((p for p in domestic_pool if counts_as_batter(p) == counts_as_batter(remove) and counts_as_bowler(p) == counts_as_bowler(remove)), None)
            if domestic is None:
                domestic = domestic_pool[0] if domestic_pool else None
            if domestic:
                selected.append(domestic)
            else:
                break
        return selected[:11]

    def enforce_role_balance(self, selected, roster, min_batters=0, min_bowlers=0):
        """Top up `selected` until it has at least `min_batters` batting options and `min_bowlers` bowling options, swapping in the best-suited bench player for the worst-suited non-matching incumbent each time (then re-applying `enforce_xi_limits`).

        Stops early (rather than looping forever) if no valid swap exists —
        e.g. a squad that genuinely can't field enough specialists.
        """
        selected = list(dict.fromkeys(selected))[:11]
        pool = sorted([p for p in roster if p not in selected], key=lambda p: p.current_ovr, reverse=True)
        def add_for(predicate, remove_key):
            candidate = next((p for p in pool if predicate(p)), None)
            if not candidate:
                return False
            removable = sorted([p for p in selected if not predicate(p)], key=remove_key)
            if not removable:
                return False
            out = removable[0]
            selected.remove(out)
            selected.append(candidate)
            pool.remove(candidate)
            pool.append(out)
            return True
        while len([p for p in selected if counts_as_batter(p)]) < min_batters:
            if not add_for(counts_as_batter, lambda p: p.current_batting):
                break
        while len([p for p in selected if counts_as_bowler(p)]) < min_bowlers:
            if not add_for(counts_as_bowler, lambda p: p.current_bowling):
                break
        return self.enforce_xi_limits(selected, roster)

    def begin_match_day(self, interactive=True):
        """Start the next match day.

        In the league stage: auto-simulates every fixture except the user's,
        then either hands the user's match to a `LiveMatch` for interactive
        play (`interactive=True`) or quick-simulates it too and advances the
        round (rolling into playoffs once round 14 completes). In the
        playoffs: unlocks the next bracket match if needed and starts a
        `LiveMatch` for it. Raises `ValueError` if the match centre isn't
        open, or (in playoffs) if the user's team isn't part of the next
        scheduled match.
        """
        if self.phase not in ("season", "playoffs"):
            raise ValueError("Match centre is not open.")
        if self.live_match and self.live_match.status != "complete":
            return
        if self.phase == "season":
            self.match_log = []
            fixtures = self.schedule[self.round_num - 1]
            user_fixture = next(pair for pair in fixtures if self.user_team_name in pair)
            for team_a, team_b in fixtures:
                if (team_a, team_b) == user_fixture:
                    continue
                self.simulate_match_auto(self.find_team(team_a), self.find_team(team_b), "League")
            if interactive:
                self.live_match = LiveMatch(self, self.find_team(user_fixture[0]), self.find_team(user_fixture[1]), "League")
            else:
                self.simulate_match_auto(self.find_team(user_fixture[0]), self.find_team(user_fixture[1]), "League")
                self.round_num += 1
                if self.round_num > 14:
                    self.finish_league_stage()
        else:
            match = self.playoff_matches[self.playoff_index]
            if match["status"] == "locked":
                self.unlock_playoff_match()
                match = self.playoff_matches[self.playoff_index]
            if self.user_team_name not in (match["team1"], match["team2"]):
                raise ValueError("Your team is not in the next playoff. Use Quick Sim Next Playoff.")
            self.live_match = LiveMatch(self, self.find_team(match["team1"]), self.find_team(match["team2"]), match["name"])

    def complete_live_match(self):
        """Acknowledge the finished live match: advance the league round (rolling into playoffs at round 15) or record the playoff result, then clear `live_match`.

        Raises `ValueError` if there's no completed live match to close out.
        """
        if not self.live_match or self.live_match.status != "complete":
            raise ValueError("Live match is not complete.")
        if self.phase == "season":
            card = self.live_match.card
            self.round_num += 1
            if self.round_num > 14:
                self.finish_league_stage()
            else:
                self.status_message = self._round_result_message(self.round_num - 1, [card])
        else:
            self.record_playoff_result(self.live_match.card["winner"])
        self.live_match = None

    def simulate_match_auto(self, team1, team2, stage):
        """Run an entire match to completion without any user interaction (used for non-user fixtures and "quick sim").

        Builds lineups for both sides — using the user's saved presets when
        their team is involved, falling back to `smart_*` selections
        otherwise — sets a default bowling plan and Impact Player choice, and
        plays it out over-by-over on autopilot. Returns the finished
        `LiveMatch`.
        """
        match = LiveMatch(self, team1, team2, stage)
        return match.auto_finish()

    def _round_result_message(self, round_num, completed):
        """Builds a status message describing the user's result for a just-finished week.

        Prefers the user's own match (`{winner} {margin} vs {rival}`),
        falling back to a generic "Week N complete" if the user's team
        wasn't part of any of the just-simulated cards (e.g. the week had
        already been resolved).
        """
        user_card = next((card for card in completed if self.user_team_name in (card["team1"], card["team2"])), None)
        if not user_card:
            return f"Week {round_num} complete."
        rival = user_card["team2"] if user_card["team1"] == self.user_team_name else user_card["team1"]
        if user_card["winner"] == self.user_team_name:
            return f"Week {round_num}: {self.user_team_name} {user_card['margin']} vs {rival}."
        return f"Week {round_num}: {self.user_team_name} lost to {rival} ({user_card['margin']})."

    def simulate_current_round(self):
        """Quick-sim everything left to resolve the current round/match without launching an interactive `LiveMatch`.

        In the league stage: finishes an in-progress live match (or simulates
        the user's fixture fresh) and the rest of the round in one go,
        advancing to the next round (or playoffs) and updating the status
        message; if no live match exists yet, simulates the entire round's 5
        fixtures. In the playoffs: unlocks and simulates the next bracket
        match and records its result.
        """
        if self.phase == "season":
            if self.live_match:
                if self.live_match.status != "complete":
                    card = self.live_match.auto_finish()
                    self.live_match = None
                else:
                    card = self.live_match.card
                    self.live_match = None
                self.round_num += 1
                if self.round_num > 14:
                    self.finish_league_stage()
                else:
                    self.status_message = self._round_result_message(self.round_num - 1, [card])
                return
            self.match_log = []
            completed = []
            for team_a, team_b in self.schedule[self.round_num - 1]:
                card = self.simulate_match_auto(self.find_team(team_a), self.find_team(team_b), "League")
                completed.append(card)
            self.round_num += 1
            if self.round_num > 14:
                self.finish_league_stage()
            else:
                self.status_message = self._round_result_message(self.round_num - 1, completed)
        elif self.phase == "playoffs":
            if self.live_match and self.live_match.status != "complete":
                card = self.live_match.auto_finish()
            elif self.live_match:
                card = self.live_match.card
            else:
                match = self.playoff_matches[self.playoff_index]
                if match["status"] == "locked":
                    self.unlock_playoff_match()
                    match = self.playoff_matches[self.playoff_index]
                card = self.simulate_match_auto(self.find_team(match["team1"]), self.find_team(match["team2"]), match["name"])
            self.live_match = None
            self.record_playoff_result(card["winner"])

    def finish_league_stage(self):
        """Close out the 14-round league stage: snapshot final standings, record the qualifying top four, and move to "league_complete" awaiting the user to start playoffs."""
        self.last_standings = self.standings()
        self.pending_playoff_top_four = [t.name for t in self.last_standings[:4]]
        self.phase = "league_complete"
        self.live_match = None
        qualified = self.user_team_name in self.pending_playoff_top_four
        self.status_message = "League stage complete. Review the table and season stats, then start playoffs." if qualified else "League stage complete. Your team missed the top four; review the season, then start or quick-sim playoffs."

    def start_playoffs(self):
        """Set up the IPL playoff bracket from the qualifying top four and open the playoffs phase. Raises `ValueError` if the league stage hasn't finished yet."""
        if self.phase != "league_complete":
            raise ValueError("Playoffs are not ready to start.")
        top_names = self.pending_playoff_top_four or [t.name for t in self.standings()[:4]]
        self.setup_playoffs([self.find_team(name) for name in top_names])
        self.match_log = []
        self.live_match = None
        self.status_message = "Playoffs are ready. Enter the Match Hub if your team is playing, or quick-sim playoff matches one at a time."

    def setup_playoffs(self, top_four):
        """Lay out the standard IPL playoff bracket from the top-four-ranked teams: Qualifier 1 (1st vs 2nd) and the Eliminator (3rd vs 4th) start open; Qualifier 2 and the Final start "locked" until their participants are decided."""
        p1, p2, p3, p4 = top_four
        self.phase = "playoffs"
        self.playoff_index = 0
        self.playoff_results = []
        self.playoff_matches = [
            {"name": "Qualifier 1", "team1": p1.name, "team2": p2.name, "status": "pending"},
            {"name": "Eliminator", "team1": p3.name, "team2": p4.name, "status": "pending"},
            {"name": "Qualifier 2", "team1": "", "team2": "", "status": "locked"},
            {"name": "Final", "team1": "", "team2": "", "status": "locked"},
        ]

    def record_playoff_result(self, winner):
        """Mark the just-finished playoff match complete, store its result, and either advance to the next bracket match (unlocking it if needed) or — once the Final is done — crown the champion and move to the post-season retention window."""
        match = self.playoff_matches[self.playoff_index]
        loser = match["team2"] if winner == match["team1"] else match["team1"]
        match.update({"status": "complete", "winner": winner, "loser": loser})
        self.playoff_results.append({"name": match["name"], "winner": winner, "loser": loser})
        self.playoff_index += 1
        if self.playoff_index >= len(self.playoff_matches):
            self.archive_season(winner, loser)
            self.phase = "season_end"
            self.status_message = f"{winner} are Season {self.season_year} champions. Retention window is next."
        else:
            self.unlock_playoff_match()
            self.status_message = f"{match['name']}: {winner} beat {loser}. Next playoff match unlocked."

    def unlock_playoff_match(self):
        """Fill in the participants for Qualifier 2 (Q1 loser vs Eliminator winner) and the Final (Q1 winner vs Q2 winner) once their feeder matches have results — the standard IPL bracket progression."""
        if self.playoff_index == 2 and self.playoff_matches[2]["status"] == "locked":
            self.playoff_matches[2].update({"team1": self.playoff_results[0]["loser"], "team2": self.playoff_results[1]["winner"], "status": "pending"})
        if self.playoff_index == 3 and self.playoff_matches[3]["status"] == "locked":
            self.playoff_matches[3].update({"team1": self.playoff_results[0]["winner"], "team2": self.playoff_results[2]["winner"], "status": "pending"})

    def open_retention(self):
        """Open the post-season retention window: alternate the keep-limit between a normal reset (`RETAIN_NORMAL`) and a deeper reset (`RETAIN_RESET`) every other season, mirroring the IPL's periodic mega-auction cycle.

        Raises `ValueError` if the season hasn't actually finished.
        """
        if self.phase != "season_end":
            raise ValueError("Retention opens after the season ends.")
        self.completed_seasons += 1
        self.retention_limit = RETAIN_RESET if self.completed_seasons % 2 == 0 else RETAIN_NORMAL
        self.phase = "retention"
        self.status_message = f"Retention window: keep {self.retention_limit} players."

    def submit_retentions(self, names):
        """Apply the user's retention choices and roll every franchise into next season's mega draft.

        For the user's team, keeps exactly the named players; CPU teams keep
        their best players by `mvp_score` (tie-broken by rating, then youth).
        Released players return to the pool as free agents. All retained and
        released players age up and reset their season stats
        (`apply_offseason_progression`/`reset_stats`), team season records
        reset to zero, ~30 fresh "regen" prospects are generated, and a new
        draft begins in **reverse-standings order with no snake** — a
        deliberate IPL-style mechanic that gives the previous season's
        weakest teams first crack at the now-thinned player pool.
        Raises `ValueError` if retention isn't open or the wrong number of
        names was submitted.
        """
        if self.phase != "retention":
            raise ValueError("Retention window is closed.")
        if len(names) != self.retention_limit:
            raise ValueError(f"Choose exactly {self.retention_limit} players.")
        reverse_order = self.standings(reverse=False)
        user_team = self.user_team()
        for team in self.teams:
            if team == user_team:
                keep = [next((p for p in team.roster if p.name == name), None) for name in names]
                keep = [p for p in keep if p]
            else:
                keep = sorted(team.roster, key=lambda p: (self.mvp_score(p), p.current_ovr, -p.age), reverse=True)[:self.retention_limit]
            release = [p for p in team.roster if p not in keep]
            for player in release:
                player.team_name = "Unassigned"
            self.player_pool.extend(release)
            team.roster = keep
            team.captain = team.captain if team.captain in keep else None
            team.vice_captain = team.vice_captain if team.vice_captain in keep else None
            team.points = team.wins = team.losses = 0
            team.runs_scored = team.balls_faced = team.runs_conceded = team.balls_bowled = 0
            for player in team.roster:
                player.apply_offseason_progression()
                player.reset_stats()
            for player in release:
                player.apply_offseason_progression()
                player.reset_stats()
        self.add_regens()
        self.season_year += 1
        self.phase = "draft"
        self.draft_type = "retention"
        self.draft_order = reverse_order
        self.draft_round = 1
        self.draft_index = 0
        self.pick_num = 1
        self.draft_history = []
        self.round_num = 1
        self.playoff_matches = []
        self.playoff_results = []
        self.live_match = None
        self.status_message = "Post-retention draft is reverse standings, no snake."
        self.cpu_until_user()

    def add_regens(self):
        """Generate ~30 fresh young prospects (age 18-21, randomly rolled ratings/profile by role, names suffixed with "*" to mark them as regens) and add them to the free-agent pool ahead of the next mega draft, replenishing talent lost to retirement/release."""
        for i in range(30):
            role = random.choice(["Batsman", "Bowler (Fast)", "Bowler (Spin)", "All-Rounder", "Wicketkeeper"])
            if role == "Batsman":
                bat, bowl = random.randint(62, 75), random.randint(8, 22)
            elif role == "Wicketkeeper":
                bat, bowl = random.randint(61, 74), random.randint(8, 14)
            elif "Bowler" in role:
                bat, bowl = random.randint(8, 24), random.randint(62, 75)
            else:
                bat, bowl = random.randint(58, 73), random.randint(58, 73)
            base = max(bat, bowl) if role != "All-Rounder" else (bat + bowl) // 2
            is_overseas = random.random() < 0.2
            batting_archetype = "Aggressor" if role in ("Batsman", "Wicketkeeper") and bat >= 70 else ("Finisher" if role == "All-Rounder" else "Defensive Tailender")
            bowling_phase = "Middle Overs" if "Spin" in role else ("New Ball" if "Fast" in role else ("Flexible" if role == "All-Rounder" else "Part-time"))
            bowling_type = "Left-arm Orthodox" if role == "Bowler (Spin)" else ("Right-arm Fast" if role == "Bowler (Fast)" else ("Right-arm Medium" if role == "All-Rounder" else "None"))
            self.player_pool.append(Player(
                self.generated_name(is_overseas), role, base, bat, bowl, is_overseas,
                random.randint(18, 21), random.choice(["Right", "Left"]),
                random.choice(["Right", "Left"]) if role not in ("Batsman", "Wicketkeeper") else "None",
                batting_archetype, bowling_phase, bowling_type,
                "Emerging talent with adaptable T20 skills",
                "Unproven against elite pressure moments",
            ))

    def generated_name(self, is_overseas):
        """Generate a unique regen player name (Indian or overseas name pools depending on `is_overseas`), suffixed with "*" to flag it as a generated player and distinguish it from real-world names in `players.csv`."""
        existing = {p.name for p in self.player_pool}
        for team in self.teams:
            existing.update(p.name for p in team.roster)
        first_names = OVERSEAS_FIRST_NAMES if is_overseas else INDIAN_FIRST_NAMES
        last_names = OVERSEAS_LAST_NAMES if is_overseas else INDIAN_LAST_NAMES
        for _ in range(20):
            candidate = f"{random.choice(first_names)} {random.choice(last_names)} *"
            if candidate not in existing:
                return candidate
        return f"{random.choice(first_names)} {random.choice(last_names)} {random.randint(2, 99)} *"

    def select_motm(self, batting, bowling, players, winner):
        """Pick the Man of the Match from this game's batting/bowling figures.

        Scores every involved player on a runs/strike-rate/wickets/economy
        blend, then strongly prefers a standout performer from the winning
        side — but allows a losing-side player to take it instead if they
        produced a clearly "legacy" performance (a century or 5-wicket haul)
        that decisively outscores the best winning performance, mirroring how
        real-world MOTM voting occasionally rewards a heroic losing effort.
        Falls back to the winning side's best-rated player if no one's match
        figures resolve to a real player (e.g. a rain-shortened/odd game).
        """
        lookup = {p.name: p for p in players}
        for player in self.all_players() + list(getattr(self, "player_pool", [])):
            lookup.setdefault(player.name, player)
        scores = {}
        for name, data in batting.items():
            scores[name] = scores.get(name, 0) + data["runs"] + data["fours"] * 2 + data["sixes"] * 3 + (15 if data["runs"] >= 50 else 0) + (25 if data["runs"] >= 100 else 0)
        for name, data in bowling.items():
            econ = data["runs"] / (data["balls"] / 6) if data["balls"] else 12
            scores[name] = scores.get(name, 0) + data["wickets"] * 30 + max(0, 8 - econ) * 5 + (18 if data["wickets"] >= 4 else 0)
        scores = {name: score for name, score in scores.items() if lookup.get(name)}
        if not scores:
            return sorted(winner.roster, key=lambda p: p.current_ovr, reverse=True)[0]
        winning_scores = {name: score for name, score in scores.items() if lookup[name].team_name == winner.name}
        if not winning_scores:
            return lookup[max(scores, key=scores.get)]
        winning_name = max(winning_scores, key=winning_scores.get)
        overall_name = max(scores, key=scores.get)
        overall_player = lookup[overall_name]
        legacy_bat = batting.get(overall_name, {}).get("runs", 0) >= 100
        legacy_bowl = bowling.get(overall_name, {}).get("wickets", 0) >= 5
        winning_notable = winning_scores[winning_name] >= 55
        if overall_player.team_name != winner.name and (legacy_bat or legacy_bowl) and not winning_notable and scores[overall_name] >= winning_scores[winning_name] + 35:
            return overall_player
        return lookup[winning_name]

    def update_bowling_bests(self, bowlers, stats, against_name=""):
        """Update each bowler's career-best bowling figures (most wickets, fewest runs as the tiebreak) if this match's spell beats their existing record, recording who it came against."""
        for player in bowlers:
            ensure_stat_fields(player)
            data = stats.get(player.name)
            if data and (data["wickets"] > player.stats["best_bowling_wickets"] or (data["wickets"] == player.stats["best_bowling_wickets"] and data["runs"] < player.stats["best_bowling_runs"])):
                player.stats["best_bowling_wickets"] = data["wickets"]
                player.stats["best_bowling_runs"] = data["runs"]
                player.stats["best_bowling_against"] = against_name

    def innings_card(self, innings):
        """Build the JSON scorecard for one completed innings: top performers (4 best batters/bowlers for the summary view) plus the full batting/bowling lineups with computed economy and "not out"/"did not bat" labels for the detailed view."""
        batting = sorted(innings["bat_stats"].items(), key=lambda x: (x[1]["runs"], -x[1]["balls"]), reverse=True)[:4]
        bowling = sorted(
            innings["bowl_stats"].items(),
            key=lambda x: (x[1]["wickets"], -(x[1]["runs"] / (x[1]["balls"] / 6) if x[1]["balls"] else 99)),
            reverse=True,
        )[:4]
        batting_order = innings.get("batting_order", [])
        dismissals = innings.get("dismissals", {})
        full_batting = [
            {"name": n, "dismissal": dismissals.get(n, "not out" if innings["bat_stats"][n].get("balls", 0) else "did not bat"), **innings["bat_stats"][n]}
            for n in batting_order if n in innings["bat_stats"]
        ]
        full_bowling = [
            {"name": n, **d, "overs": f"{d['balls'] // 6}.{d['balls'] % 6}", "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0}
            for n, d in innings["bowl_stats"].items()
        ]
        return {
            "team": innings["team"].name,
            "against": innings["bowling_team"].name,
            "score": f"{innings['runs']}/{innings['wickets']}",
            "batting": [{"name": n, **d} for n, d in batting],
            "bowling": [{"name": n, **d, "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0} for n, d in bowling],
            "full_batting": full_batting,
            "full_bowling": full_bowling,
            "impact_sub": innings.get("impact_sub", ""),
            "over_log": innings.get("over_log", []),
        }

    def archive_season(self, champion, runner_up):
        """Snapshot the just-finished season into `season_history`: champion, runner-up, season MVP, final points table, top batting/bowling leaderboards, and the full set of award-race leaderboards — preserved across the retention/draft reset that follows."""
        mvp = self.leaderboard(lambda p: self.mvp_score(p), True, None, 1)[0]
        self.season_history.append({
            "season": self.season_year,
            "champion": champion,
            "runner_up": runner_up,
            "mvp": mvp,
            "points_table": [self.team_dict(t) for t in self.standings()],
            "batting": self.batting_table()[:15],
            "bowling": self.bowling_table()[:15],
            "leaderboards": self.leaderboards(),
            "playoffs": list(self.playoff_results),
        })

    def mvp_score(self, player):
        """Season-long value heuristic for ranking players (retention priority, MVP award, leaderboards): a weighted blend of run-scoring and strike-rate bonus, wicket-taking and economy bonus, fielding contributions, MOTM awards, and a "won games while playing" share — rewarding well-rounded, winning contributions over single-category stuffing."""
        ensure_stat_fields(player)
        s = player.stats
        batting = s["runs"] + s["fours"] * 2 + s["sixes"] * 3 + s["fifties"] * 8 + s["hundreds"] * 18
        if s["balls_faced"] >= 30:
            batting += max(0, player.batting_strike_rate - 135) * 0.25
        bowling = s["wickets"] * 26
        if s["balls_bowled"] >= 18:
            bowling += max(0, 8.2 - player.bowling_economy) * 8
        bowling += max(0, s["best_bowling_wickets"] - 2) * 12
        fielding = s["catches"] * 4 + s["stumpings"] * 7 + s["runouts"] * 8
        win_share = s.get("team_wins", 0) * 4 + max(0, s.get("games", 0) - s.get("team_wins", 0)) * 1
        return batting + bowling + fielding + s["motm"] * 35 + win_share

    def all_players(self):
        """Every player currently on a franchise roster (excludes free agents in `player_pool`)."""
        players = []
        for team in self.teams:
            players.extend(team.roster)
        return players

    def find_player_anywhere(self, name):
        """Look up a player by name across rosters first, then the free-agent pool. Returns `None` if not found anywhere."""
        for player in self.all_players():
            if player.name == name:
                return player
        for player in getattr(self, "player_pool", []):
            if player.name == name:
                return player
        return None

    def player_dict(self, player):
        """Serialise a player into the rich JSON dict the frontend uses for rosters, draft cards, lineup pickers, and profile views.

        Beyond raw ratings/stats, computes derived figures (average, bowling
        average/strike rate), season rating-progression strings, and
        dynamically generated strength/weakness notes that reflect this
        season's in-form/out-of-form trends (overriding the player's static
        profile text once they've faced/bowled enough deliveries to be
        meaningful) plus phase-fit summaries for each match phase.
        """
        ensure_stat_fields(player)
        s = player.stats
        avg = s["runs"] / s["outs"] if s["outs"] else float(s["runs"])
        bowl_avg = s["runs_conceded"] / s["wickets"] if s["wickets"] else 0
        bowl_sr = s["balls_bowled"] / s["wickets"] if s["wickets"] else 0
        strength_note = getattr(player, "strengths", "")
        weakness_note = getattr(player, "weaknesses", "")
        if s["balls_faced"] >= 30 and player.batting_strike_rate >= 155:
            strength_note = "In-season boundary tempo trending up"
        elif s["balls_faced"] >= 30 and player.batting_strike_rate < 115:
            weakness_note = "In-season scoring tempo under pressure"
        if s["balls_bowled"] >= 18 and player.bowling_economy and player.bowling_economy <= 7.2:
            strength_note = "In-season control and wicket pressure"
        elif s["balls_bowled"] >= 18 and player.bowling_economy >= 10:
            weakness_note = "In-season expensive spells against hitters"
        bowling_type = getattr(player, "bowling_type", "None")
        allrounder_style = ""
        if player.role == "All-Rounder":
            allrounder_style = "Spin AR" if any(x in bowling_type for x in ("Spin", "Orthodox", "Leg", "Off")) else "Pace AR"
        return {
            "name": player.name, "role": player.role, "age": player.age, "team": player.team_name,
            "base_ovr": player.base_ovr, "ovr": player.current_ovr, "bat": player.current_batting,
            "bowl": player.current_bowling, "form": round(player.form, 1), "overseas": player.is_overseas,
            "ovr_progression": f"{getattr(player, 'season_start_ovr', player.base_ovr)} -> {player.current_ovr}",
            "bat_progression": f"{getattr(player, 'season_start_bat', player.batting_ovr)} -> {player.current_batting}",
            "bowl_progression": f"{getattr(player, 'season_start_bowl', player.bowling_ovr)} -> {player.current_bowling}",
            "batting_hand": player.batting_hand, "bowling_hand": player.bowling_hand,
            "preferred_position": getattr(player, "preferred_position", 6),
            "batting_archetype": expanded_batting_archetype(player),
            "bowling_phase": expanded_bowling_phase(player),
            "bowling_type": getattr(player, "bowling_type", "None"),
            "allrounder_style": allrounder_style,
            "strengths": strength_note,
            "weaknesses": weakness_note,
            "phase_fit_powerplay": phase_fit_label(player, "Powerplay"),
            "phase_fit_middle": phase_fit_label(player, "Middle Overs"),
            "phase_fit_death": phase_fit_label(player, "Death Overs"),
            "runs": s["runs"], "balls": s["balls_faced"], "outs": s["outs"], "avg": round(avg, 2),
            "sr": round(player.batting_strike_rate, 2), "hs": s["highest_score"], "fours": s["fours"],
            "hs_against": s.get("highest_score_against", ""),
            "sixes": s["sixes"], "boundaries": s["fours"] + s["sixes"], "fifties": s["fifties"],
            "hundreds": s["hundreds"], "wickets": s["wickets"], "runs_conceded": s["runs_conceded"],
            "balls_bowled": s["balls_bowled"], "econ": round(player.bowling_economy, 2),
            "bowling_avg": round(bowl_avg, 2), "bowling_sr": round(bowl_sr, 2),
            "maidens": s["maidens"], "motm": s["motm"], "best_bowling": self.best_bowling_label(player),
            "best_bowling_against": s.get("best_bowling_against", ""),
            "catches": s["catches"], "stumpings": s["stumpings"], "runouts": s["runouts"],
            "games": s.get("games", 0), "team_wins": s.get("team_wins", 0),
            "mvp": round(self.mvp_score(player), 1),
        }

    def best_bowling_label(self, player):
        """Format a player's career-best bowling figures as "wickets/runs" (e.g. "4/22"), or "-" if they've never taken a wicket."""
        ensure_stat_fields(player)
        wkts = player.stats["best_bowling_wickets"]
        runs = player.stats["best_bowling_runs"]
        return f"{wkts}/{runs}" if wkts else "-"

    def team_dict(self, team):
        """Serialise a franchise into the JSON dict the frontend uses for standings, squad, and lineup-planning views: branding, season record/NRR, leadership, saved/suggested lineups and orders, the Starting XI + Impact Sub, and the full roster (best-rated first)."""
        # A user-renamed team keeps its original branding (abbr/colors) via
        # `meta_name`; team_meta falls back to neutral defaults for a custom name.
        meta = team_meta(team)
        saved_batting = list(getattr(team, "saved_batting_order_names", []))
        saved_bowling = list(getattr(team, "saved_bowling_over_names", []))
        roster_ready = len(team.roster) >= 11
        roster_names = {p.name for p in team.roster}

        # The user's explicitly saved Starting XI is returned VERBATIM — its
        # slot order is the batting order they chose, so we must not re-sort it.
        saved_xi = list(getattr(team, "saved_starting_xi_names", []))
        starting_xi = [name for name in saved_xi if name in roster_names]
        has_saved_xi = len(starting_xi) == 11 and len(set(starting_xi)) == 11
        if not roster_ready:
            starting_xi = []
        elif has_saved_xi:
            pass  # complete, valid saved XI — keep verbatim.
        elif saved_xi:
            # Partial saved XI (roster changed under it): keep the still-valid
            # picks in their saved slot order and fill only the gaps, rather
            # than wiping the user's whole lineup back to the autofill default.
            starting_xi = self.complete_starting_xi(team, saved_xi)
        else:
            # No saved XI yet: build the smart default and present it in natural
            # batting order (openers first, tail last) so the slot-by-slot
            # editor reads as a sensible lineup rather than raw selection order.
            smart_xi = self.smart_starting_xi(team)
            xi_players = [next((p for p in team.roster if p.name == name), None) for name in smart_xi]
            xi_players = [p for p in xi_players if p]
            starting_xi = [p.name for p in self.smart_batting_order(xi_players)] if len(xi_players) == 11 else smart_xi

        impact_sub_name = getattr(team, "saved_impact_sub_name", "")
        if roster_ready and (impact_sub_name not in roster_names or impact_sub_name in starting_xi):
            impact_sub_name = self.smart_impact_sub(team, starting_xi)
        elif not roster_ready:
            impact_sub_name = ""

        return {
            "name": team.name, "abbr": meta["abbr"], "home": meta["home"], "primary": meta["primary"], "accent": meta["accent"],
            "points": team.points, "wins": team.wins, "losses": team.losses, "played": team.games_played,
            "nrr": round(team.net_run_rate, 3), "captain": team.captain.name if team.captain else "",
            "vice_captain": team.vice_captain.name if team.vice_captain else "",
            "saved_batting_order": saved_batting,
            "saved_bowling_order": saved_bowling,
            "starting_xi": starting_xi,
            "impact_sub_name": impact_sub_name,
            "saved_wicketkeeper": getattr(team, "saved_wicketkeeper_name", ""),
            "suggested_batting_order": saved_batting or (self.default_batting_order(team) if roster_ready else []),
            "suggested_bowling_order": saved_bowling or (self.default_bowling_plan(team) if roster_ready else []),
            "roster": [self.player_dict(p) for p in sorted(team.roster, key=lambda x: x.current_ovr, reverse=True)],
        }

    def leaderboard(self, key, reverse=True, minimum=None, limit=20):
        """Rank all rostered players by `key` (a sort-key function), optionally filtering to those meeting a `(stat_name, minimum_value)` qualification threshold (e.g. a minimum-balls cutoff for batting/bowling tables), and return up to `limit` as serialised player dicts."""
        players = self.all_players()
        if minimum:
            stat, value = minimum
            players = [p for p in players if p.stats.get(stat, 0) >= value]
        ranked = sorted(players, key=key, reverse=reverse)
        if limit is not None:
            ranked = ranked[:limit]
        return [self.player_dict(p) for p in ranked]

    def batting_table(self):
        """Full season run-scoring leaderboard (the "Orange Cap" race), ranked by runs then overall season value, restricted to players who've actually faced a ball."""
        return self.leaderboard(lambda p: (p.stats["runs"], self.mvp_score(p)), True, ("balls_faced", 1), None)

    def bowling_table(self):
        """Full season wicket-taking leaderboard (the "Purple Cap" race), ranked by wickets then overall season value, restricted to players who've actually bowled a ball."""
        return self.leaderboard(lambda p: (p.stats["wickets"], self.mvp_score(p)), True, ("balls_bowled", 1), None)

    def payload(self):
        """Serialise the entire league state into the JSON dict the frontend renders for whatever screen is active — title, draft room, season hub, live match, retention, or season history.

        Bundles together team/standings data, the live match payload (if
        any), draft state and available pool, schedule/results, season
        leaderboards, and history — essentially everything the single-page
        frontend needs to redraw itself after any action.
        """
        available = sorted(self.player_pool, key=lambda p: p.current_ovr, reverse=True)
        current = self.current_draft_team()
        user = self.user_team() if self.teams and self.user_team_name else None
        return {
            "save_exists": bool(self.list_saves()) or os.path.exists(SAVE_FILE),
            "save_name": self.save_name,
            "phase": self.phase, "season": self.season_year, "completed_seasons": self.completed_seasons,
            "draft_type": self.draft_type, "round": self.round_num, "user_team": self.user_team_name,
            "difficulty": self.difficulty, "draft_pool_type": self.draft_pool_type,
            "status": self.status_message, "teams": [self.team_dict(t) for t in self.teams],
            "standings": [self.team_dict(t) for t in self.standings()] if self.teams else [],
            "squad_size": SQUAD_SIZE, "retention_limit": self.retention_limit,
            "draft": {
                "round": self.draft_round, "pick": self.pick_num, "current_team": current.name if current else "",
                "started": getattr(self, "draft_started", True),
                "user_pick_position": self.draft_order.index(user) + 1 if user and user in self.draft_order else 0,
                "available": [self.player_dict(p) for p in available],
                "history": self.draft_history[-120:],
                "needs": self.roster_needs(user) if user and self.phase == "draft" else {},
            },
            "retention": {"players": [self.player_dict(p) for p in user.roster] if user else []},
            "schedule": self.schedule, "playoffs": self.playoff_matches, "playoff_index": self.playoff_index,
            "match_log": self.match_log[-40:], "fixture_results": getattr(self, "fixture_results", [])[-120:],
            "live_match": self.live_match.payload() if self.live_match else None,
            "history": self.season_history,
            "tables": {"batting": self.batting_table() if self.teams else [], "bowling": self.bowling_table() if self.teams else []},
            "leaderboards": self.leaderboards() if self.teams else {},
        }

    def leaderboards(self):
        """Build the full set of season award-race leaderboards (Orange/Purple Cap, sixes, fours, strike rate, economy, fielding, MVP, etc.) shown on the stats screen, each independently ranked and qualification-filtered where relevant (e.g. minimum balls faced/bowled for rate-based stats)."""
        return {
            "orange_cap": self.leaderboard(lambda p: p.stats["runs"], limit=50),
            "purple_cap": self.leaderboard(lambda p: p.stats["wickets"], limit=50),
            "sixes": self.leaderboard(lambda p: p.stats["sixes"], limit=50),
            "fours": self.leaderboard(lambda p: p.stats["fours"], limit=50),
            "boundaries": self.leaderboard(lambda p: p.stats["fours"] + p.stats["sixes"], limit=50),
            "highest_score": self.leaderboard(lambda p: p.stats["highest_score"], limit=50),
            "strike_rate": self.leaderboard(lambda p: p.batting_strike_rate, True, ("balls_faced", 30), 50),
            "economy": self.leaderboard(lambda p: p.bowling_economy or 99, False, ("balls_bowled", 18), 50),
            "best_figures": self.leaderboard(lambda p: (p.stats.get("best_bowling_wickets", 0), -p.stats.get("best_bowling_runs", 999)), limit=50),
            "catches": self.leaderboard(lambda p: p.stats["catches"], limit=50),
            "stumpings": self.leaderboard(lambda p: p.stats["stumpings"], limit=50),
            "runouts": self.leaderboard(lambda p: p.stats["runouts"], limit=50),
            "mvp": self.leaderboard(lambda p: self.mvp_score(p), limit=50),
        }

    # --- User-facing renaming (roster editor) ---------------------------------

    def _all_player_names(self):
        return {p.name for t in self.teams for p in t.roster} | {p.name for p in self.player_pool}

    def rename_player(self, old_name, new_name):
        """Rename a player everywhere in this career (roster object + all saved
        presets, leadership, and stored match/history references).

        Raises ValueError if `old_name` doesn't exist, `new_name` is blank, or
        `new_name` already belongs to a different player. The change is global
        to this career only — it's how a user restores a real name if they want.
        """
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("Name cannot be empty.")
        if old_name == new_name:
            return
        existing = self._all_player_names()
        if old_name not in existing:
            raise ValueError("That player isn't in this league.")
        if new_name in existing:
            raise ValueError("Another player already has that name.")

        # Update the Player objects (rosters + free-agent pool).
        for p in [pl for t in self.teams for pl in t.roster] + list(self.player_pool):
            if p.name == old_name:
                p.name = new_name
        # Update every saved string reference held on the teams.
        for team in self.teams:
            _replace_in_obj(team, old_name, new_name)
        # Update name strings buried in the serialised history/result collections.
        self._deep_rename(old_name, new_name)

    def rename_team(self, old_name, new_name):
        """Rename a franchise everywhere in this career (Team object, the user's
        team pointer, schedule/standings/results/history references)."""
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("Name cannot be empty.")
        if old_name == new_name:
            return
        team_names = {t.name for t in self.teams}
        if old_name not in team_names:
            raise ValueError("That team isn't in this league.")
        if new_name in team_names:
            raise ValueError("Another team already has that name.")

        for team in self.teams:
            if team.name == old_name:
                # Preserve the original branding key so the franchise keeps its
                # abbr/colors after a rename (team_dict looks meta up by this).
                if not getattr(team, "meta_name", None):
                    team.meta_name = old_name
                team.name = new_name
        if self.user_team_name == old_name:
            self.user_team_name = new_name
        # Update player.team_name back-pointers + buried history references.
        for p in [pl for t in self.teams for pl in t.roster] + list(self.player_pool):
            if getattr(p, "team_name", None) == old_name:
                p.team_name = new_name
        self._deep_rename(old_name, new_name)

    def _deep_rename(self, old_name, new_name):
        """Replace an exact name string anywhere in the JSON-serialisable career
        collections (schedule, fixture/playoff results, match log, season
        history, draft history). These hold names as plain strings, so a deep
        walk catches references that aren't reachable as Player/Team objects."""
        self.schedule = _deep_replace(self.schedule, old_name, new_name)
        self.fixture_results = _deep_replace(self.fixture_results, old_name, new_name)
        self.playoff_matches = _deep_replace(self.playoff_matches, old_name, new_name)
        self.playoff_results = _deep_replace(self.playoff_results, old_name, new_name)
        self.match_log = _deep_replace(self.match_log, old_name, new_name)
        self.season_history = _deep_replace(self.season_history, old_name, new_name)
        self.draft_history = _deep_replace(self.draft_history, old_name, new_name)


def _replace_in_obj(team, old_name, new_name):
    """Replace `old_name` with `new_name` in a Team's saved name-string fields."""
    if team.saved_impact_sub_name == old_name:
        team.saved_impact_sub_name = new_name
    if team.saved_wicketkeeper_name == old_name:
        team.saved_wicketkeeper_name = new_name
    for attr in (
        "saved_playing_xi_names",
        "saved_starting_xi_names",
        "saved_batting_order_names",
        "saved_bowling_over_names",
    ):
        names = getattr(team, attr, None)
        if names:
            setattr(team, attr, [new_name if n == old_name else n for n in names])
    # captain / vice_captain are Player objects already renamed via the roster.


def _deep_replace(value, old_name, new_name):
    """Recursively replace exact `old_name` strings within lists/tuples/dicts."""
    if isinstance(value, str):
        return new_name if value == old_name else value
    if isinstance(value, list):
        return [_deep_replace(v, old_name, new_name) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_replace(v, old_name, new_name) for v in value)
    if isinstance(value, dict):
        return {k: _deep_replace(v, old_name, new_name) for k, v in value.items()}
    return value
