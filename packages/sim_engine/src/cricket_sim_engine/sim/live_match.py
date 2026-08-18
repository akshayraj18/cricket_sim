"""Single-match driver: toss, lineups, over-by-over simulation, and scorecards.

`LiveMatch` owns everything about one match end-to-end, calling into
`MatchEngine` purely for per-ball outcome sampling while it manages the
state machine (`status`), lineups/orders/bowling plans, the live scoreboard,
super overs, impact substitutions, and the final scorecard payload.
"""
import random

from cricket_sim_engine.engine import MatchEngine
from cricket_sim_engine.sim.constants import team_meta, format_config
from cricket_sim_engine.sim.helpers import (
    ensure_stat_fields,
    innings_phase,
    is_batting_role,
    is_bowling_role,
    is_wicketkeeper_option,
    counts_as_batter,
    counts_as_bowler,
    wickets_margin,
)


class LiveMatch:
    """Drives a single match from toss through to the final scorecard.

    Owns the per-innings score state, lineups/orders/bowling plans for both
    teams, the `MatchEngine` used to sample ball outcomes, and (when needed)
    the super-over tiebreaker. `status` is the state machine driving the UI:
    "toss" -> "lineup" -> "live" -> ... -> "complete" (with "batting_order",
    "innings_break", "super_over*" as intermediate/branch states). `payload()`
    serialises all of this into the JSON the frontend renders.
    """

    def __init__(self, league, team1, team2, stage):
        self.league = league
        self.team1 = team1
        self.team2 = team2
        self.stage = stage
        self.match_format = getattr(league, "match_format", "t20")
        self.format = format_config(self.match_format)
        self.engine = MatchEngine(league.user_team_name, getattr(league, "difficulty", "hard"))
        self.engine.match_format = self.match_format
        self.toss_winner = random.choice([team1, team2])
        self.decision = None
        self.status = "toss"
        self.message = f"{self.toss_winner.name} won the toss."
        self.inn1_bat = None
        self.inn1_bowl = None
        self.xis = {}
        self.pending_swaps = {}
        self.batting_orders = {}
        self.bowling_pools = {}
        self.bowling_plan_for = {}
        self.wicketkeepers = {}
        self.current_innings = 1
        self.target = None
        self.innings = []
        self.score = None
        self.card = None
        self.super_over = None
        self.impact_subs = []
        # Test-only day/session pacing. Unused (and never read) by any
        # T20/ODI match — `self.format["days"] == 1` for those, so none of
        # the day/session branches in play_over/close_current_over ever fire.
        self.current_day = 1
        self.current_session = 1
        self.overs_bowled_in_session = 0
        self.pending_session_break = False
        self.follow_on_available = False
        self.followed_on = False
        self.declared = {}
        if self.toss_winner.name != league.user_team_name:
            self.choose_toss(random.choice(["bat", "bowl"]))

    def choose_toss(self, decision):
        """Record the toss-winner's bat/bowl decision, set up the first innings' batting/bowling sides, and auto-build CPU lineups.

        Raises `ValueError` if the toss was already decided or `decision`
        isn't "bat"/"bowl".
        """
        if self.status != "toss":
            raise ValueError("Toss is already complete.")
        if decision not in ("bat", "bowl"):
            raise ValueError("Choose bat or bowl.")
        self.decision = decision
        toss_loser = self.team2 if self.toss_winner == self.team1 else self.team1
        self.inn1_bat = self.toss_winner if decision == "bat" else toss_loser
        self.inn1_bowl = toss_loser if decision == "bat" else self.toss_winner
        self.status = "lineup"
        self.message = f"{self.toss_winner.name} chose to {decision} first."
        self.auto_cpu_xis()

    def auto_cpu_xis(self):
        """Build playing XI, batting order, bowling pool, and keeper for every CPU-controlled team in this match (the user's team waits for `set_user_xi`)."""
        for team in (self.team1, self.team2):
            if team.name != self.league.user_team_name:
                xi = self.league.smart_cpu_xi(team)
                self.xis[team.name] = xi
                self.batting_orders[team.name] = self.league.smart_batting_order(xi)
                self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
                self.bowling_plan_for[team.name] = []
                self.wicketkeepers[team.name] = self.default_keeper(team, xi)

    def auto_finish(self):
        """Drive this match to completion on autopilot from whatever state it's currently in.

        Used when the user quick-sims a match they've already started in the
        hub: resolves any pending toss/lineup/impact/next-batter/super-over
        choices using the same saved-preset and smart-default logic as a
        from-scratch auto-sim (so the user's confirmed XI and in-progress
        score are preserved rather than discarded), then plays out the rest
        ball by ball. Returns the finished `card`.
        """
        if self.status == "toss":
            self.choose_toss(random.choice(["bat", "bowl"]))
        for team in (self.team1, self.team2):
            if team.name not in self.xis:
                if team.name == self.league.user_team_name:
                    xi = self.user_preset_xi(team)
                else:
                    xi = self.league.smart_cpu_xi(team)
                self.xis[team.name] = xi
                saved_order = getattr(team, "saved_batting_order_names", []) if team.name == self.league.user_team_name else []
                if saved_order:
                    # Honour the user's saved batting order, appending any XI
                    # member not covered by it (e.g. after a roster change).
                    order = [p for p in xi if p.name in saved_order]
                    order.sort(key=lambda p: saved_order.index(p.name))
                    order += [p for p in xi if p not in order]
                else:
                    # No saved order: use the same smart batting order the squad
                    # screen displays, so a quick-sim plays the lineup the user
                    # sees rather than the raw XI-selection order. (Previously
                    # this fell through to resolve-order because `order` already
                    # had 11 players, which is why presets only "took" after one
                    # manual Save.)
                    order = self.league.smart_batting_order(xi)
                self.batting_orders[team.name] = order if len(order) == 11 else self.league.smart_batting_order(xi)
                self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
                self.wicketkeepers.setdefault(team.name, self.default_keeper(team, xi))
                if team.name == self.league.user_team_name:
                    self.set_bowling_plan(team, getattr(team, "saved_bowling_over_names", []))
        self.start_first_innings_if_ready()
        if self.status == "batting_order" and self.league.user_team().name in self.xis:
            self.start_second_innings()
        while self.status not in ("complete", "super_over_setup"):
            # Auto-clear session/stumps breaks so auto_finish runs to completion
            # without stalling. Interactive play shows the break prompt to the
            # user; autopilot just acknowledges it immediately.
            if self.pending_session_break:
                self.pending_session_break = False
            while self.status == "next_batter" and self.score and self.score.get("pending_next_batter"):
                order = self.score["batting_order"]
                idx = self.score["striker_idx"]
                self.select_next_batter(order[idx].name)
                while self.status == "over":
                    self.play_over(auto=True)
                if self.pending_session_break:
                    self.pending_session_break = False
            while self.status == "over":
                self.play_over(auto=True)
                if self.pending_session_break:
                    self.pending_session_break = False
            if self.status == "follow_on_decision":
                # Autopilot always enforces the follow-on when it's on offer —
                # matches a CPU captain's default real-world choice.
                self.decide_follow_on(enforce=True)
            if self.status == "impact":
                user_team = self.league.user_team()
                # The 11+1 Impact Player swap is a one-time-per-match
                # allowance (`pending_swaps` models exactly one pairing), so a
                # Test match's later innings breaks (it can have up to three)
                # decline the swap rather than incorrectly reapplying the same
                # pairing again.
                if self.current_innings <= 2:
                    swap_out, swap_in = self.pending_swaps.get(user_team.name, (None, None))
                else:
                    swap_out, swap_in = None, None
                self.apply_impact_sub(out_name=swap_out, in_name=swap_in, auto=True)
            while self.status == "over":
                self.play_over(auto=True)
                if self.pending_session_break:
                    self.pending_session_break = False
            if self.status == "batting_order" and self.league.user_team().name in self.xis:
                self.start_second_innings()
            elif self.status not in ("next_batter", "over", "follow_on_decision", "impact"):
                break
        if self.status == "super_over_setup":
            self.auto_missing_super_over_lineups()
            self.play_super_over()
        return self.card

    def user_preset_xi(self, team):
        """Build the user's playing XI for an autopilot match under the 11+1 model: the Starting XI (with the Impact Sub already swapped in for innings 1 if bowling first), stashing the at-the-break swap pairing in `pending_swaps`."""
        batting_first = team == self.inn1_bat
        xi_names, swap_out, swap_in = self.league.resolve_match_xi(team, batting_first)
        self.pending_swaps[team.name] = (swap_out, swap_in)
        xi = [next((p for p in team.roster if p.name == name), None) for name in xi_names]
        return [p for p in xi if p]

    def update_pending_swap(self, team, xi):
        """Recompute `pending_swaps[team.name]` for the user's confirmed innings-1 XI.

        Starts from the default `(swap_out, swap_in)` pairing for `team`'s
        saved Starting XI/Impact Sub (`resolve_match_xi`). If the user's
        confirmed `xi` differs from the saved Starting XI by exactly one
        player, that one-player difference becomes the pairing instead — the
        player missing from `xi` is `swap_out` (returns at the break) and the
        extra player in `xi` is `swap_in` (leaves at the break), mirroring
        the default's "one player swaps at the break" structure either way.
        """
        batting_first = team == self.inn1_bat
        _, default_out, default_in = self.league.resolve_match_xi(team, batting_first)
        starting_xi = set(getattr(team, "saved_starting_xi_names", [])) or set(self.league.smart_starting_xi(team))
        confirmed = {p.name for p in xi}
        missing = starting_xi - confirmed
        extra = confirmed - starting_xi
        if len(missing) == 1 and len(extra) == 1:
            self.pending_swaps[team.name] = (next(iter(extra)), next(iter(missing)))
        else:
            self.pending_swaps[team.name] = (default_out, default_in)

    def default_keeper(self, team, xi):
        """Pick a wicketkeeper for `xi`: prefer the team's previously saved keeper if still selected, else the best-batting keeper option, else just the first player."""
        saved = getattr(team, "saved_wicketkeeper_name", "")
        keeper = next((p for p in xi if p.name == saved and is_wicketkeeper_option(p)), None)
        if keeper:
            return keeper
        return sorted([p for p in xi if is_wicketkeeper_option(p)], key=lambda p: p.current_batting, reverse=True)[0] if any(is_wicketkeeper_option(p) for p in xi) else xi[0]

    def default_batting_order(self, xi):
        """Delegate to `LeagueState.smart_batting_order` for a sensible default order when the user hasn't set one."""
        return self.league.smart_batting_order(xi)

    def suggested_roster(self, bowling_first=False):
        """The user's roster sorted to surface the most useful picks first for lineup selection.

        When `bowling_first` is set (the user's team will bowl first), bowling
        options and bowling rating take priority; otherwise batting does.
        """
        team = self.league.user_team()
        if bowling_first:
            return sorted(team.roster, key=lambda p: (0 if is_bowling_role(p) else 1, -p.current_bowling, -p.current_ovr))
        return sorted(team.roster, key=lambda p: (0 if is_batting_role(p) else 1, -p.current_batting, -p.current_ovr))

    def set_user_xi(self, names, batting_order=None, bowling_order=None, intents=None, save=False, context="batting", wicketkeeper_name=""):
        """Confirm the user's playing XI (and, depending on `status`, kick off the relevant innings).

        Validates squad-composition rules (exactly 11 players, at most 4
        overseas, minimum batting/bowling options for the side that's
        batting/bowling first), records intents/keeper/order, and stores a
        20-ball bowling plan if `bowling_order` forms a valid one (see
        `set_bowling_plan`). When `save` is set, the selections are cached on
        the `Team` so the UI can offer to reuse them next match. If this is
        the second-innings lineup (`status == "batting_order"`), starts that
        innings; otherwise starts the first innings once both XIs are ready,
        deriving the at-the-break Impact Sub swap pairing for `pending_swaps`.
        Raises `ValueError` on any composition-rule violation or if lineup
        selection isn't currently open. The `context` arg is accepted for
        backward call-site compatibility but the validation branch is derived
        from `lineup_context()`.
        """
        if self.status not in ("lineup", "batting_order"):
            raise ValueError("Lineup selection is not open.")
        team = self.league.user_team()
        if self.status == "batting_order" and team.name in self.xis:
            xi = self.xis[team.name]
        else:
            xi = [next((p for p in team.roster if p.name == name), None) for name in names]
            xi = [p for p in xi if p]
        if len(xi) != 11:
            raise ValueError("Pick exactly 11 players.")
        if sum(1 for p in xi if p.is_overseas) > 4:
            raise ValueError("Playing XI cannot include more than 4 overseas players.")
        bowling_first = self.status == "lineup" and team == self.inn1_bowl
        if not bowling_first and len([p for p in xi if counts_as_batter(p)]) < 6:
            raise ValueError("Starting XI needs at least 6 batting options including all-rounders and wicketkeepers.")
        if bowling_first and len([p for p in xi if counts_as_bowler(p)]) < 4:
            raise ValueError("Starting XI needs at least 4 bowling options including all-rounders.")
        for player in xi:
            player.intent = (intents or {}).get(player.name, "Normal")
        order_names = batting_order or names
        order = [next((p for p in xi if p.name == name), None) for name in order_names]
        order = [p for p in order if p]
        if len(order) != 11:
            order = self.default_batting_order(xi)
        self.xis[team.name] = xi
        keeper = next((p for p in xi if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None) or self.default_keeper(team, xi)
        self.wicketkeepers[team.name] = keeper
        self.batting_orders[team.name] = order
        self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
        self.set_bowling_plan(team, bowling_order or [])
        if self.status == "lineup":
            self.update_pending_swap(team, xi)
        if save:
            team.saved_playing_xi_names = [p.name for p in xi]
            team.saved_wicketkeeper_name = keeper.name
            team.saved_batting_order_names = [p.name for p in order]
            if bowling_order:
                team.saved_bowling_over_names = list(bowling_order)
        if self.status == "batting_order":
            self.start_second_innings()
            return
        self.start_first_innings_if_ready()

    def set_bowling_plan(self, team, names):
        """Store a pre-planned bowling order for `team` if `names` forms a valid one (one entry per over of the innings, each bowler appearing at most the format's per-bowler over cap); otherwise clear the plan and fall back to per-over bowler selection."""
        valid = [p.name for p in self.bowling_pools.get(team.name, [])]
        clean = [name for name in names if name in valid]
        overs = self.format["overs_per_innings"]
        cap = self.format["bowler_overs_cap"]
        if len(clean) == overs and all(clean.count(name) <= cap for name in set(clean)):
            self.bowling_plan_for[team.name] = clean
        else:
            self.bowling_plan_for[team.name] = []

    def start_first_innings_if_ready(self):
        """Once both teams have a confirmed XI (and no innings has yet begun), begin the first innings."""
        if self.innings or self.score:
            return
        if self.team1.name in self.xis and self.team2.name in self.xis:
            self.start_innings(self.inn1_bat, self.inn1_bowl, self.batting_orders[self.inn1_bat.name], self.bowling_pools[self.inn1_bowl.name])

    def start_innings(self, batting_team, bowling_team, batting_order, bowling_pool):
        """Initialise live score state for a new innings and set `status` to "live"."""
        self.score = {
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "batting_order": batting_order,
            "bowling_pool": bowling_pool,
            "runs": 0,
            "wickets": 0,
            "balls": 0,
            "striker_idx": 0,
            "non_striker_idx": 1,
            "last_bowler": None,
            "overs_tracked": {},
            "bat_stats": {p.name: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in batting_order},
            "bowl_stats": {p.name: {"runs": 0, "wickets": 0, "balls": 0} for p in bowling_pool},
            "dismissals": {},
            "partnership_runs": 0,
            "partnership_balls": 0,
            "over_log": [],
            "current_over_events": [],
            "active_bowler": None,
            # Default aggression is format-specific: ODI batters start
            # conservatively (2) and ramp up; Test batters are very cautious (1).
            # T20 stays at 3 (the existing baseline).
            "batting_aggression": {p.name: (1 if self.match_format == "test" else 2 if self.match_format == "odi" else 3) for p in batting_order},
            "bowling_aggression": {p.name: 2 for p in bowling_pool},
            "pending_next_batter": False,
        }
        # Per-batter balls-faced this innings (for settling-in / fatigue tracking).
        for p in batting_order:
            p.balls_faced_this_innings = 0
        # Per-bowler consecutive overs without rest (for fatigue tracking).
        for p in bowling_pool:
            p.bowler_consecutive_overs = 0
        self.status = "over"
        self.message = f"{batting_team.name} innings started. Pick the next bowler."

    def available_bowlers(self):
        """Bowlers eligible to bowl the next over, best phase-fit first.

        Excludes anyone who has already bowled their format's per-bowler over
        allowance (4 for T20, 10 for ODI, effectively uncapped for Test) and
        (when possible) whoever bowled the previous over, since the same
        bowler can't deliver consecutive overs. Falls back to progressively
        looser pools (allow the previous bowler, then allow capped bowlers)
        if no one else is left — keeps the match playable in edge cases like
        a side carrying very few specialist bowlers.

        For Test/ODI, a hard consecutive-over ceiling forces rotation: no
        bowler can bowl more than 4 consecutive overs (Test) or 5 (ODI) —
        mirroring real captaincy, where even a dominant bowler gets rested
        after a spell to manage fatigue and maintain pace.
        """
        if self.status != "over" or not self.score:
            return []
        tracked = self.score["overs_tracked"]
        last = self.score["last_bowler"]
        cap = self.format["bowler_overs_cap"]
        match_format = getattr(self, "match_format", "t20")
        # Hard consecutive-over ceiling: Test=4, ODI=5, T20=uncapped (over cap handles it)
        consec_ceil = {"test": 4, "odi": 5}.get(match_format, 999)
        options = [
            p for p in self.score["bowling_pool"]
            if tracked.get(p.name, 0) < cap
            and p != last
            and getattr(p, "bowler_consecutive_overs", 0) < consec_ceil
        ]
        if not options:
            # Relax consecutive ceiling but still exclude same bowler and capped
            options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < cap and p != last]
        if not options:
            options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < cap]
        if not options:
            options = list(self.score["bowling_pool"])
        phase = innings_phase(self.score["balls"] // 6, self.format["phase_boundaries"])
        return sorted(options, key=lambda p: self.bowler_phase_score(p, phase), reverse=True)

    def cpu_bowler(self):
        """The CPU's choice of next bowler: simply the best phase-fit option from `available_bowlers`."""
        return self.available_bowlers()[0]

    def bowler_phase_score(self, player, phase):
        """Heuristic score for how well this bowler suits the given match phase, used to rank/select CPU bowling options.

        Starts from the bowler's rating, adds bonuses for phase specialisation,
        and subtracts a fatigue penalty for bowlers who have bowled many
        consecutive overs without rest (Test/ODI cricket mandates rotation).
        """
        score = player.current_bowling
        bowling_type = getattr(player, "bowling_type", "")
        bowling_phase = getattr(player, "bowling_phase", "Flexible")
        if bowling_phase == phase:
            score += 8
        if phase in ("Powerplay", "Death Overs") and ("Fast" in bowling_type or "Swing" in bowling_type or "Medium" in bowling_type or "Seam" in bowling_type):
            score += 5
        if phase == "Middle Overs" and ("Spin" in bowling_type or "Orthodox" in bowling_type or "Leg" in bowling_type or "Off" in bowling_type):
            score += 6
        if phase == "Death Overs" and "Variations" in bowling_type:
            score += 5
        # Fatigue penalty for consecutive overs (harder in Test/ODI):
        consecutive = getattr(player, "bowler_consecutive_overs", 0)
        if consecutive >= 2:
            match_format = getattr(self, "match_format", "t20")
            penalty_per_over = {"test": 10, "odi": 7}.get(match_format, 4)
            score -= (consecutive - 1) * penalty_per_over

        # Workload distribution: in Test/ODI, the CPU should spread overs across
        # all available bowlers so no one dominates just by having a higher base
        # rating. Over-bowled bowlers get a scaled-down score so fillers become
        # more attractive as the innings progresses.
        match_format = getattr(self, "match_format", "t20")
        if match_format in ("test", "odi") and self.score:
            tracked = self.score.get("overs_tracked", {})
            pool = self.score.get("bowling_pool", [])
            pool_bowlers = [p for p in pool if getattr(p, "current_bowling", 0) > 0]
            if pool_bowlers:
                total_overs = sum(tracked.get(p.name, 0) for p in pool_bowlers)
                my_overs = tracked.get(player.name, 0)
                avg_overs = total_overs / len(pool_bowlers) if pool_bowlers else 0
                overuse = my_overs - avg_overs
                if overuse > 0:
                    workload_penalty = {"test": 6, "odi": 4}.get(match_format, 0)
                    score -= overuse * workload_penalty
        return score

    def ensure_active_bowler(self, bowler_name=None, auto=False):
        """Resolve and record who bowls the upcoming over, choosing a new bowler only when one isn't already mid-over.

        If the user controls the bowling side (and `auto` isn't forced), uses
        `bowler_name` or the pre-planned bowler for this over (falling back to
        the top `available_bowlers` pick), raising `ValueError` if the choice
        isn't eligible. Otherwise lets the CPU pick. Updates the per-bowler
        over count and resets the current-over event log.
        """
        if self.status != "over":
            raise ValueError("No over is ready.")
        if self.score.get("active_bowler") and self.score["balls"] % 6 != 0:
            return self.score["active_bowler"]
        bowling_team = self.score["bowling_team"]
        user_bowling = bowling_team.name == self.league.user_team_name and not auto
        bowler = None
        if user_bowling:
            planned = self.planned_bowler_name()
            chosen_name = bowler_name or planned
            bowler = next((p for p in self.available_bowlers() if p.name == chosen_name), None)
            if not bowler and not bowler_name:
                bowler = self.available_bowlers()[0]
            if not bowler:
                raise ValueError("Choose an eligible bowler.")
        else:
            bowler = self.cpu_bowler()

        prev_bowler = self.score.get("last_bowler")
        self.score["last_bowler"] = bowler
        self.score["overs_tracked"][bowler.name] = self.score["overs_tracked"].get(bowler.name, 0) + 1
        self.score["active_bowler"] = bowler
        self.score["current_over_events"] = []
        # Fatigue tracking: reset consecutive count for any bowler who just had a
        # break, then increment for whoever is bowling now.
        if prev_bowler and prev_bowler != bowler:
            prev_bowler.bowler_consecutive_overs = 0
        bowler.bowler_consecutive_overs = getattr(bowler, "bowler_consecutive_overs", 0) + 1
        return bowler

    def play_over(self, bowler_name=None, auto=False, max_balls=6, stop_on_wicket=True):
        """Simulate up to `max_balls` deliveries (capped at the current over's remaining balls), advancing match state ball by ball.

        Stops early when the innings/chase ends, or — for the user's batting
        side, when `stop_on_wicket` is set and not auto-simulating — when a
        wicket falls, switching `status` to "next_batter" so the user can pick
        who comes in. At the end of an over (or innings), closes the over log
        and either finishes the innings or updates `message` with the latest
        scoreline.
        """
        if self.status != "over":
            raise ValueError("No over is ready.")
        if self.innings_is_over():
            self.finish_innings()
            return
        bowler = self.ensure_active_bowler(bowler_name, auto)
        start_balls = self.score["balls"]
        balls_cap = self.format["balls_per_innings"]
        end_ball = min(((start_balls // 6) + 1) * 6, start_balls + max_balls, balls_cap)
        self.score["last_event_wicket"] = False
        while self.score["balls"] < end_ball and not self.innings_is_over():
            if self.target and self.score["runs"] >= self.target:
                break
            event = self.play_ball(bowler)
            self.score["current_over_events"].append(event)
            self.score["last_event_wicket"] = event["kind"] == "wicket"
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name and self.score["wickets"] < 10 and self.score["balls"] < balls_cap:
                self.score["pending_next_batter"] = True
                self.status = "next_batter"
                self.message = f"{event['description']}. Choose who comes in next."
                return
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name:
                break

        if self.score["balls"] % 6 == 0 or self.score["balls"] >= balls_cap or self.innings_is_over() or (self.target and self.score["runs"] >= self.target):
            self.close_current_over()

        if self.score["balls"] >= balls_cap or self.innings_is_over() or (self.target and self.score["runs"] >= self.target) or self.match_time_expired():
            self.finish_innings()
        else:
            marker = "End of over" if self.score["balls"] % 6 == 0 else "Ball complete"
            self.message = f"{marker} {self.score['balls'] // 6}.{self.score['balls'] % 6}: {self.scoreline()}."

    def innings_is_over(self):
        """Whether the batting side is "all out" — i.e. has lost one fewer wicket than it has batters in the order (so the last player can't bat alone)."""
        if not self.score:
            return False
        order_len = len(self.score.get("batting_order", []))
        all_out_wickets = min(10, max(0, order_len - 1))
        return self.score.get("wickets", 0) >= all_out_wickets

    def match_time_expired(self):
        """Whether a Test match has used up its scheduled days/sessions (the real-cricket "stumps on the final day" cutoff), independent of any single innings' all-out/balls-cap state.

        Always `False` for T20/ODI (`self.format["innings_per_side"] == 1`, so
        the match is never time-limited — only the per-innings balls cap
        matters there). For Test, true once the final scheduled session's
        overs quota has been used up — this is what lets a 4th-innings chase
        end in a draw instead of grinding on to the engine's 90-over-per-innings
        ceiling.
        """
        if self.format["innings_per_side"] <= 1:
            return False
        on_final_session = self.current_day >= self.format["days"] and self.current_session >= self.format["sessions_per_day"]
        return on_final_session and self.overs_bowled_in_session >= self.format["overs_per_session"]

    def close_current_over(self):
        """Append the just-finished over's bowler/events/runs to `over_log` and clear the active-over tracking state."""
        bowler = self.score.get("active_bowler")
        events = list(self.score.get("current_over_events", []))
        if bowler and events:
            over_runs = sum(e.get("runs", 0) for e in events)
            over_number = (self.score["balls"] + 5) // 6
            self.score["over_log"].append({"over": over_number, "bowler": bowler.name, "events": events, "runs": over_runs})
        self.score["active_bowler"] = None
        self.score["current_over_events"] = []
        if self.format["innings_per_side"] > 1:
            self.advance_test_session()

    def advance_test_session(self):
        """Track Test-match day/session progress: one over just closed, so tick the session's over counter and flag a stumps/session break once it hits the format's overs-per-session quota.

        Does nothing once the match has reached its final scheduled day/session
        (the innings-end / balls-cap logic in `play_over` is what actually
        stops play there) — this only manages the *break* between sessions
        within an ongoing innings.
        """
        self.overs_bowled_in_session += 1
        if self.overs_bowled_in_session >= self.format["overs_per_session"]:
            on_final_session = self.current_day >= self.format["days"] and self.current_session >= self.format["sessions_per_day"]
            if on_final_session:
                # Time's up for the whole match — leave overs_bowled_in_session
                # at its maxed-out value so match_time_expired() can see it;
                # play_over's innings-end check (not a session-break prompt)
                # is what actually stops play here.
                return
            self.overs_bowled_in_session = 0
            if self.current_session < self.format["sessions_per_day"]:
                self.current_session += 1
            else:
                self.current_day += 1
                self.current_session = 1
            self.pending_session_break = True

    def proceed_session(self):
        """Acknowledge a stumps/session break and resume play. Raises `ValueError` if no break is currently pending."""
        if not self.pending_session_break:
            raise ValueError("No session break is pending.")
        self.pending_session_break = False
        label = "Stumps" if self.current_session == 1 else "Session break"
        self.message = f"{label}. Day {self.current_day}, Session {self.current_session} of {self.format['sessions_per_day']}. {self.scoreline() if self.score else ''}"

    def set_aggression(self, batting=None, bowling=None):
        """Update per-player batting/bowling aggression dials (clamped to 1-5) for whichever named players are part of the current innings; ignored if no innings is live."""
        if not self.score:
            return
        for name, value in (batting or {}).items():
            if name in self.score["batting_aggression"]:
                self.score["batting_aggression"][name] = max(1, min(5, int(value)))
        for name, value in (bowling or {}).items():
            if name in self.score["bowling_aggression"]:
                self.score["bowling_aggression"][name] = max(1, min(5, int(value)))

    def select_next_batter(self, name):
        """Slot the user's chosen replacement batter into the upcoming position in the order, then resume play.

        Swaps the chosen (not-yet-batted) player into the next striker slot —
        letting the user bat them ahead of their original order position — and
        clears the "next_batter" wait state. Closes the over first if the
        wicket fell on the last ball of an over. Raises `ValueError` if no
        wicket is currently waiting on a replacement, or the named player has
        already batted / isn't in the order.
        """
        if self.status != "next_batter" or not self.score.get("pending_next_batter"):
            raise ValueError("No wicket is waiting for a next batter.")
        order = self.score["batting_order"]
        next_idx = self.score["striker_idx"]
        chosen_idx = next((i for i, p in enumerate(order) if p.name == name and i >= next_idx), None)
        if chosen_idx is None:
            raise ValueError("Choose an available batter who has not batted yet.")
        order[next_idx], order[chosen_idx] = order[chosen_idx], order[next_idx]
        self.score["pending_next_batter"] = False
        self.status = "over"
        if self.score["balls"] % 6 == 0:
            self.close_current_over()
        self.message = f"{order[next_idx].name} walks in next. {self.scoreline()}."

    def planned_bowler_name(self):
        """The bowler the bowling side pre-planned for the over about to start, or `None` if there's no plan or it doesn't cover this over."""
        team_name = self.score["bowling_team"].name
        plan = self.bowling_plan_for.get(team_name, [])
        over_index = self.score["balls"] // 6
        if over_index < len(plan):
            return plan[over_index]
        return None

    def play_ball(self, bowler):
        """Simulate one delivery: sample an outcome from `MatchEngine`, apply it to score/stats/strike, and return an event dict describing it.

        Tags the striker and bowler with the current `match_phase` and their
        configured aggression before sampling, since `MatchEngine.simulate_ball`
        reads those to bias its outcome distribution. On a wicket, resolves the
        dismissal type (see `resolve_dismissal`), advances past the dismissed
        batter, and resets the partnership; on runs, updates running totals and
        rotates the strike on 1s/3s and at the end of the over. Returns a dict
        of shape `{"kind": "wicket"|"runs"|"innings_end", ...}`.
        """
        batting_order = self.score["batting_order"]
        if self.innings_is_over() or self.score["striker_idx"] >= len(batting_order):
            self.score["wickets"] = max(self.score["wickets"], min(10, max(0, len(batting_order) - 1)))
            return {"kind": "innings_end", "label": "", "runs": 0}
        striker = batting_order[self.score["striker_idx"]]
        self.score["bat_stats"].setdefault(striker.name, {"runs": 0, "balls": 0, "fours": 0, "sixes": 0})
        self.score["bowl_stats"].setdefault(bowler.name, {"runs": 0, "wickets": 0, "balls": 0})
        over_num = self.score["balls"] // 6
        phase = innings_phase(over_num, self.format["phase_boundaries"])
        striker.match_phase = phase
        bowler.match_phase = phase
        striker.batting_aggression = self.score["batting_aggression"].get(striker.name, 3)
        bowler.bowling_aggression = self.score["bowling_aggression"].get(bowler.name, 2)
        # ODI/Test: auto-ramp CPU batting aggression over the innings so the
        # run rate naturally lifts in the middle and death overs (mimics how
        # real batters shift from conservative to attacking as the innings
        # progresses). Only applies to CPU-batted-for teams; the user controls
        # aggression explicitly via the set_aggression API.
        if self.match_format in ("odi", "test"):
            is_cpu_batter = self.score["batting_team"].name != self.league.user_team_name
            if is_cpu_batter or self.score["batting_team"].name == self.league.user_team_name:
                # Apply auto-ramp for all batters; user can override via set_aggression.
                saved_agg = self.score["batting_aggression"].get(striker.name)
                default_agg = 1 if self.match_format == "test" else 2
                if saved_agg == default_agg:
                    # Only ramp if still at the initial default (user hasn't manually adjusted).
                    if self.match_format == "odi":
                        if over_num >= 40:
                            striker.batting_aggression = 4
                        elif over_num >= 35:
                            striker.batting_aggression = 3
                        elif over_num >= 20:
                            striker.batting_aggression = 2
                        # else stays at 2 (conservative)
                    elif self.match_format == "test":
                        if over_num >= 70:
                            striker.batting_aggression = 3
                        elif over_num >= 40:
                            striker.batting_aggression = 2
                        # else stays at 1 (very conservative)
        # Expose per-innings balls faced to the engine for settling-in logic.
        striker.balls_faced_this_innings = self.score["bat_stats"].get(striker.name, {}).get("balls", 0)
        outcome = self.engine.simulate_ball(striker, bowler)
        self.score["balls"] += 1
        self.score["partnership_balls"] += 1
        self.score["bat_stats"][striker.name]["balls"] += 1
        self.score["bowl_stats"][bowler.name]["balls"] += 1
        striker.stats["balls_faced"] += 1
        bowler.stats["balls_bowled"] += 1
        if outcome == "W":
            dismissal = self.resolve_dismissal(striker, bowler)
            self.score["wickets"] += 1
            striker.stats["outs"] += 1
            if dismissal["bowler_gets_wicket"]:
                bowler.stats["wickets"] += 1
                self.score["bowl_stats"][bowler.name]["wickets"] += 1
            self.score["partnership_runs"] = 0
            self.score["partnership_balls"] = 0
            self.score["striker_idx"] = max(self.score["striker_idx"], self.score["non_striker_idx"]) + 1
            self.score["dismissals"][striker.name] = dismissal.get("how_out", dismissal["description"])
            return {"kind": "wicket", "label": "W", **dismissal}
        runs = int(outcome)
        self.score["runs"] += runs
        self.score["partnership_runs"] += runs
        self.score["bat_stats"][striker.name]["runs"] += runs
        self.score["bowl_stats"][bowler.name]["runs"] += runs
        striker.stats["runs"] += runs
        bowler.stats["runs_conceded"] += runs
        if runs == 4:
            striker.stats["fours"] += 1
            self.score["bat_stats"][striker.name]["fours"] += 1
        elif runs == 6:
            striker.stats["sixes"] += 1
            self.score["bat_stats"][striker.name]["sixes"] += 1
        if runs in (1, 3):
            self.score["striker_idx"], self.score["non_striker_idx"] = self.score["non_striker_idx"], self.score["striker_idx"]
        if self.score["balls"] % 6 == 0:
            self.score["striker_idx"], self.score["non_striker_idx"] = self.score["non_striker_idx"], self.score["striker_idx"]
        return {"kind": "runs", "runs": runs, "label": outcome, "batter": striker.name, "bowler": bowler.name}

    def resolve_dismissal(self, striker, bowler):
        """Decide how a wicket falls — stumped, run out, or caught — and who gets credit.

        Spinners get a chance at a stumping (crediting the keeper, with the
        bowler also getting the wicket); otherwise there's a chance of a run
        out (which scales up with the batter's aggression and credits a random
        fielder, NOT the bowler) before falling back to a catch (credited to
        the keeper or a random fielder, with the bowler also getting the
        wicket). Returns a dict describing the dismissal for the commentary
        feed and stat-keeping.
        """
        keeper = self.wicketkeepers.get(self.score["bowling_team"].name) or next((p for p in self.xis[self.score["bowling_team"].name] if is_wicketkeeper_option(p)), None)
        fielders = [p for p in self.xis[self.score["bowling_team"].name] if p != bowler]
        is_spin = "Spin" in getattr(bowler, "bowling_type", "") or "Orthodox" in getattr(bowler, "bowling_type", "") or "Spin" in bowler.role
        roll = random.random()
        batting_aggression = self.score["batting_aggression"].get(striker.name, 3)
        runout_cutoff = 0.18 + max(0, batting_aggression - 3) * 0.04
        if is_spin and keeper and roll < 0.14:
            keeper.stats["stumpings"] += 1
            return {
                "dismissal": "stumped",
                "batter": striker.name,
                "bowler": bowler.name,
                "fielder": keeper.name,
                # `how_out` omits the batter's name (the scorecard already shows
                # it); `description` keeps it for the commentary feed.
                "how_out": f"st {keeper.name} b {bowler.name}",
                "description": f"{striker.name} st {keeper.name} b {bowler.name}",
                "bowler_gets_wicket": True,
            }
        if roll < runout_cutoff:
            fielder = random.choice(fielders) if fielders else bowler
            fielder.stats["runouts"] += 1
            return {
                "dismissal": "run out",
                "batter": striker.name,
                "bowler": bowler.name,
                "fielder": fielder.name,
                "how_out": f"run out ({fielder.name})",
                "description": f"{striker.name} run out ({fielder.name})",
                "bowler_gets_wicket": False,
            }
        catcher_pool = ([keeper] * 2 if keeper else []) + fielders
        catcher = random.choice(catcher_pool) if catcher_pool else bowler
        catcher.stats["catches"] += 1
        return {
            "dismissal": "caught",
            "batter": striker.name,
            "bowler": bowler.name,
            "fielder": catcher.name,
            "how_out": f"c {catcher.name} b {bowler.name}",
            "description": f"{striker.name} c {catcher.name} b {bowler.name}",
            "bowler_gets_wicket": True,
        }

    def scoreline(self):
        """Short human-readable score string, e.g. "Mumbai Mavericks 142/3 (15.2)"."""
        overs = f"{self.score['balls'] // 6}.{self.score['balls'] % 6}"
        return f"{self.score['batting_team'].name} {self.score['runs']}/{self.score['wickets']} ({overs})"

    def finish_innings(self):
        """Close out the current innings: roll up career milestones (highest score, fifties/hundreds), update both teams' season run/ball totals (for NRR), archive the innings card, and either set the chase target and move to the second innings or complete the match.

        All-out innings count as the format's full balls-per-innings faced for
        NRR purposes (the standard cricket convention — a side bowled out is
        treated as having "used" its full quota). Test matches (more than one
        innings per side) are handled separately by `finish_test_innings`,
        since they have follow-on/declaration/draw paths a limited-overs
        match never reaches.
        """
        if self.format["innings_per_side"] > 1:
            self.finish_test_innings()
            return
        batting_team = self.score["batting_team"]
        bowling_team = self.score["bowling_team"]
        runs = self.score["runs"]
        wickets = self.score["wickets"]
        balls = self.score["balls"]
        self.archive_milestones(batting_team, bowling_team, wickets, balls, runs)
        if self.current_innings == 1:
            self.current_innings = 2
            self.target = runs + 1
            if getattr(self.league, "competition", "ipl") == "ipl":
                self.status = "impact"
                self.message = f"Innings break. Target is {self.target}. Use one Impact Player sub if you want."
            else:
                self.message = f"Innings break. Target is {self.target}."
                self.prepare_second_innings()
        else:
            self.complete_match()

    def archive_milestones(self, batting_team, bowling_team, wickets, balls, runs):
        """Shared by both the limited-overs and Test innings-close paths: roll up career milestones, update both teams' season run/ball totals (for NRR), and archive the innings card onto `self.innings`."""
        for name, data in self.score["bat_stats"].items():
            player = next((p for p in self.score["batting_order"] if p.name == name), None)
            if not player:
                continue
            if data["runs"] > player.stats["highest_score"]:
                player.stats["highest_score"] = data["runs"]
                player.stats["highest_score_against"] = bowling_team.name
            if data["runs"] >= 100:
                player.stats["hundreds"] += 1
            elif data["runs"] >= 50:
                player.stats["fifties"] += 1
        final_balls = self.format["balls_per_innings"] if wickets == 10 else balls
        batting_team.runs_scored += runs
        batting_team.balls_faced += final_balls
        bowling_team.runs_conceded += runs
        bowling_team.balls_bowled += final_balls
        self.innings.append({
            "team": batting_team,
            "bowling_team": bowling_team,
            "runs": runs,
            "wickets": wickets,
            "balls": balls,
            "bat_stats": self.score["bat_stats"],
            "bowl_stats": self.score["bowl_stats"],
            "batting_order": [p.name for p in self.score["batting_order"]],
            "dismissals": dict(self.score.get("dismissals", {})),
            "over_log": list(self.score.get("over_log", [])),
        })

    def finish_test_innings(self):
        """Close out a Test innings and advance to whatever comes next: the follow-on decision (after innings 2, if the criteria are met), the next innings, or the match result.

        Innings sequence: 1 = team A bats, 2 = team B bats, then either a
        follow-on decision (if A leads by `follow_on_margin`+) or a normal
        innings break; innings 3 and 4 follow from there. The match completes
        once 4 innings are done, the fourth-innings chase succeeds, or no
        further play is possible (handled by `complete_test_match`).
        """
        batting_team = self.score["batting_team"]
        bowling_team = self.score["bowling_team"]
        runs = self.score["runs"]
        wickets = self.score["wickets"]
        balls = self.score["balls"]
        self.archive_milestones(batting_team, bowling_team, wickets, balls, runs)

        ipl = getattr(self.league, "competition", "ipl") == "ipl"

        if self.current_innings == 1:
            self.current_innings = 2
            if ipl:
                self.status = "impact"
                self.message = "Innings break. Use one Impact Player sub if you want."
            else:
                self.message = "Innings break."
                self.start_second_innings()
            return

        if self.current_innings == 2:
            team_a_runs = self.innings[0]["runs"]
            team_b_runs = self.innings[1]["runs"]
            lead = team_a_runs - team_b_runs
            margin = self.format["follow_on_margin"]
            if margin and lead >= margin:
                self.follow_on_available = True
                self.current_innings = 3
                self.status = "follow_on_decision"
                self.message = f"{self.inn1_bat.name} lead by {lead} runs and can enforce the follow-on."
                return
            self.current_innings = 3
            if ipl:
                self.status = "impact"
                self.message = "Innings break. Use one Impact Player sub if you want."
            else:
                self.message = "Innings break."
                self.start_second_innings()
            return

        if self.current_innings == 3:
            if self.followed_on and self.innings[2]["team"] == self.inn1_bowl and self.innings[2]["runs"] < (self.innings[0]["runs"] - self.innings[1]["runs"]):
                # Follow-on enforced and the follow-on side's 2nd innings
                # still falls short of team A's 1st-innings lead — an innings
                # win, no 4th innings needed.
                self.complete_test_match()
                return
            self.current_innings = 4
            if ipl:
                self.status = "impact"
                self.message = "Innings break. Use one Impact Player sub if you want."
            else:
                self.message = "Innings break."
                self.start_second_innings()
            return

        self.complete_test_match()

    def decide_follow_on(self, enforce=True):
        """Resolve the follow-on decision after Test innings 2: enforce it (team B bats again straight away) or decline it (team A bats again normally)."""
        if self.status != "follow_on_decision":
            raise ValueError("No follow-on decision is pending.")
        self.followed_on = bool(enforce)
        ipl = getattr(self.league, "competition", "ipl") == "ipl"
        if self.followed_on:
            msg = f"{self.inn1_bowl.name} follow on."
        else:
            msg = f"{self.inn1_bat.name} bat again."
        if ipl:
            self.status = "impact"
            self.message = msg + " Use one Impact Player sub if you want."
        else:
            self.message = msg
            self.start_second_innings()

    def declare_innings(self):
        """End the batting side's innings early by their own choice (Test only). Raises `ValueError` if it isn't currently the user's innings live, or the format doesn't allow declarations."""
        if self.format["innings_per_side"] <= 1:
            raise ValueError("Declarations are only available in Test matches.")
        if self.status != "over" or not self.score:
            raise ValueError("No innings is in progress to declare.")
        self.declared[self.current_innings] = True
        self.finish_innings()

    def setup_super_over(self):
        """Initialise a Super Over tiebreaker after a tied match: the side that bowled first innings bats first, CPU lineups are pre-picked, and `status` moves to "super_over_setup" awaiting the user's selection."""
        self.super_over = {
            "batting_first": self.inn1_bowl,
            "batting_second": self.inn1_bat,
            "batters": {},
            "bowlers": {},
            "innings": [],
            "winner": "",
            "message": f"Match tied. Super Over: {self.inn1_bowl.name} bat first.",
        }
        for team in (self.team1, self.team2):
            if team.name != self.league.user_team_name:
                self.super_over["batters"][team.name] = self.cpu_super_batters(team)
                self.super_over["bowlers"][team.name] = self.cpu_super_bowler(team)
        self.status = "super_over_setup"
        self.message = self.super_over["message"]

    def cpu_super_batters(self, team):
        """The CPU's three Super Over batters: best-batting picks, with a bonus for Finisher/Aggressor archetypes that suit a 6-ball burst."""
        xi = self.xis.get(team.name, self.league.smart_cpu_xi(team))
        return sorted(xi, key=lambda p: (p.current_batting + (8 if getattr(p, "batting_archetype", "") in ("Finisher", "Aggressor") else 0), p.current_ovr), reverse=True)[:3]

    def cpu_super_bowler(self, team):
        """The CPU's Super Over bowler: best death-overs phase fit from the bowling-capable XI (or the whole XI if no specialists)."""
        pool = [p for p in self.xis.get(team.name, []) if is_bowling_role(p)] or self.xis.get(team.name, [])
        return sorted(pool, key=lambda p: (self.bowler_phase_score(p, "Death Overs"), p.current_ovr), reverse=True)[0]

    def auto_missing_super_over_lineups(self):
        """Fill in CPU Super Over batters/bowler for any team that doesn't have one chosen yet (used as a safety net before simulating)."""
        for team in (self.team1, self.team2):
            self.super_over["batters"].setdefault(team.name, self.cpu_super_batters(team))
            self.super_over["bowlers"].setdefault(team.name, self.cpu_super_bowler(team))

    def set_super_over_lineup(self, batter_names, bowler_name):
        """Confirm the user's three Super Over batters and one bowler, then immediately simulate the Super Over.

        Raises `ValueError` if Super Over selection isn't open, fewer/more
        than three unique batters are chosen, or the named bowler isn't an
        eligible bowling option in the user's XI.
        """
        if self.status != "super_over_setup":
            raise ValueError("Super Over selection is not open.")
        team = self.league.user_team()
        xi = self.xis.get(team.name, [])
        batters = [next((p for p in xi if p.name == name), None) for name in batter_names]
        batters = [p for p in batters if p]
        if len(batters) != 3 or len({p.name for p in batters}) != 3:
            raise ValueError("Pick exactly three unique Super Over batters.")
        bowlers = [p for p in xi if is_bowling_role(p)]
        bowler = next((p for p in bowlers if p.name == bowler_name), None)
        if not bowler:
            raise ValueError("Pick one eligible Super Over bowler.")
        self.super_over["batters"][team.name] = batters
        self.super_over["bowlers"][team.name] = bowler
        self.play_super_over()

    def play_super_over(self):
        """Simulate both Super Over innings and decide the match winner.

        The chasing side wins outright by beating the target; otherwise the
        higher score wins. A second tie is broken by a 50/50 coin flip (the
        "reserve day"-style tiebreak this sim uses instead of another Super
        Over), and the match is finalized either way.
        """
        first_team = self.super_over["batting_first"]
        second_team = self.super_over["batting_second"]
        first = self.simulate_super_over_innings(first_team, self.super_over["bowlers"][second_team.name])
        second = self.simulate_super_over_innings(second_team, self.super_over["bowlers"][first_team.name], target=first["runs"] + 1)
        self.super_over["innings"] = [first, second]
        if second["runs"] >= first["runs"] + 1:
            winner = second_team
            loser = first_team
            margin = "won in the Super Over"
        elif first["runs"] > second["runs"]:
            winner = first_team
            loser = second_team
            margin = "won in the Super Over"
        else:
            winner = first_team if random.random() < 0.5 else second_team
            loser = second_team if winner == first_team else first_team
            margin = "won the tied Super Over on the reserve tiebreak"
        self.super_over["winner"] = winner.name
        self.finalize_match(winner, loser, margin)

    def simulate_super_over_innings(self, batting_team, bowler, target=None):
        """Simulate a single 6-ball Super Over innings and return its scorecard.

        Ends at 6 balls, 2 wickets, or (when chasing) on reaching `target`.
        Batters and bowler are pinned to "Death Overs" phase and high
        aggression, reflecting a Super Over's all-out nature, before each
        ball is sampled via `MatchEngine.simulate_ball`.
        """
        batters = self.super_over["batters"][batting_team.name]
        striker_idx, non_striker_idx, next_idx = 0, 1, 2
        runs = wickets = balls = 0
        batting = {p.name: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in batters}
        bowling = {bowler.name: {"runs": 0, "wickets": 0, "balls": 0}}
        events = []
        while balls < 6 and wickets < 2 and (not target or runs < target):
            striker = batters[striker_idx]
            striker.match_phase = "Death Overs"
            bowler.match_phase = "Death Overs"
            striker.batting_aggression = 5
            bowler.bowling_aggression = 3
            outcome = self.engine.simulate_ball(striker, bowler)
            balls += 1
            batting[striker.name]["balls"] += 1
            bowling[bowler.name]["balls"] += 1
            if outcome == "W":
                wickets += 1
                bowling[bowler.name]["wickets"] += 1
                events.append({"kind": "wicket", "label": "W", "description": f"{striker.name} out b {bowler.name}"})
                if wickets < 2:
                    striker_idx = next_idx
                continue
            ball_runs = int(outcome)
            runs += ball_runs
            batting[striker.name]["runs"] += ball_runs
            bowling[bowler.name]["runs"] += ball_runs
            if ball_runs == 4:
                batting[striker.name]["fours"] += 1
            if ball_runs == 6:
                batting[striker.name]["sixes"] += 1
            events.append({"kind": "runs", "label": outcome, "runs": ball_runs})
            if ball_runs in (1, 3):
                striker_idx, non_striker_idx = non_striker_idx, striker_idx
        return {
            "team": batting_team.name,
            "runs": runs,
            "wickets": wickets,
            "balls": balls,
            "bowler": bowler.name,
            "batting": [{"name": n, **d} for n, d in batting.items()],
            "bowling": [{"name": bowler.name, **bowling[bowler.name], "overs": f"0.{balls}", "econ": round(bowling[bowler.name]["runs"] / (balls / 6), 2) if balls else 0}],
            "events": events,
            "score": f"{runs}/{wickets}",
        }

    def apply_impact_sub(self, out_name=None, in_name=None, auto=False):
        """Optionally swap one of the user's playing-XI players for a bench player at the innings break, then move on to the second innings.

        Validates both names resolve (one currently in the XI, one on the
        bench) and that the swap doesn't push the side over the 4-overseas
        limit, then updates the XI, batting order, bowling pool, and keeper
        (re-defaulting the keeper if they were the one subbed out or are no
        longer in the XI) and logs the sub for the scorecard. Skips the swap
        entirely if no names are given — the user is allowed to decline.
        Raises `ValueError` if it isn't currently the innings break, or the
        named players can't be resolved to XI/bench members.
        """
        user_team = self.league.user_team()
        if self.status != "impact":
            raise ValueError("Impact sub is only available at innings break.")
        if out_name and in_name:
            xi = self.xis[user_team.name]
            bench = [p for p in user_team.roster if p not in xi]
            out_player = next((p for p in xi if p.name == out_name), None)
            in_player = next((p for p in bench if p.name == in_name), None)
            if not out_player or not in_player:
                raise ValueError("Choose one player from XI and one from bench.")
            leaders = {user_team.captain, user_team.vice_captain}
            keeper_name = getattr(user_team, "saved_wicketkeeper_name", "")
            if out_player in leaders or out_player.name == keeper_name:
                raise ValueError("Cannot sub out the captain, vice-captain, or wicketkeeper.")
            new_xi = [in_player if p == out_player else p for p in xi]
            if sum(1 for p in new_xi if p.is_overseas) > 4:
                raise ValueError("Impact sub would break the overseas limit.")
            self.xis[user_team.name] = new_xi
            # The post-sub XI's batting order follows the squad's saved
            # Starting XI batting order (so a returning batter reclaims their
            # usual slot); anyone not in that order (e.g. an Impact Sub bowler
            # coming in for the first time) bats at the tail.
            starting_order_names = getattr(user_team, "saved_batting_order_names", []) or self.league.default_batting_order(user_team)
            order = [p for p in new_xi if p.name in starting_order_names]
            order.sort(key=lambda p: starting_order_names.index(p.name))
            order += [p for p in new_xi if p not in order]
            self.batting_orders[user_team.name] = order[:11]
            self.bowling_pools[user_team.name] = [p for p in new_xi if is_bowling_role(p)] or new_xi
            if self.wicketkeepers.get(user_team.name) == out_player or self.wicketkeepers.get(user_team.name) not in new_xi:
                self.wicketkeepers[user_team.name] = self.default_keeper(user_team, new_xi)
            self.impact_subs.append(f"{user_team.name}: {out_player.name} out, {in_player.name} in")
        if auto:
            self.start_second_innings()
        else:
            self.prepare_second_innings()

    def next_innings_batting_team(self):
        """Which team bats in the innings about to start, given `current_innings` and (for Test) the follow-on decision.

        T20/ODI only ever reach innings 2 (the chase, always `inn1_bowl`).
        Test alternates normally — A, B, A, B (innings 3 is `inn1_bat` again,
        innings 4 is `inn1_bowl`) — unless team A enforced the follow-on, in
        which case innings 3 is `inn1_bowl` batting straight away again and
        innings 4 is `inn1_bat` chasing.
        """
        if self.current_innings == 2:
            return self.inn1_bowl
        if self.current_innings == 3:
            return self.inn1_bowl if self.followed_on else self.inn1_bat
        return self.inn1_bat if self.followed_on else self.inn1_bowl

    def _compute_test_target(self):
        """Compute and set `self.target` for the current Test innings if it's a genuine run-chase.

        In a standard 4-innings Test, the 4th innings is always a chase.
        After a follow-on the 3rd innings is also a chase (the team that
        followed on must overhaul the deficit to win).  In all other innings
        the target is irrelevant (no chase in progress), so we clear it.
        """
        if self.format["innings_per_side"] <= 1:
            return  # Not a Test match — target is set by finish_innings() already.
        n = self.current_innings
        if n <= 2:
            self.target = None
            return
        # Who is chasing in innings 3/4?
        chasing = self.next_innings_batting_team()
        chasing_innings = [inn for inn in self.innings if inn["team"] == chasing]
        defending_innings = [inn for inn in self.innings if inn["team"] != chasing]
        chasing_runs = sum(inn["runs"] for inn in chasing_innings)
        defending_runs = sum(inn["runs"] for inn in defending_innings)
        deficit = defending_runs - chasing_runs
        if deficit > 0:
            # Chasing side still needs to overhaul the defending side.
            self.target = defending_runs + 1
        else:
            # Chasing side already leads — this innings extends the lead, no target.
            self.target = None

    def prepare_second_innings(self):
        """Move to the next innings: if the user is about to bat, pause for them to set a batting order first; otherwise start the innings immediately."""
        self._compute_test_target()
        user_team = self.league.user_team()
        batting_team = self.next_innings_batting_team()
        bowling_team = self.inn1_bowl if batting_team == self.inn1_bat else self.inn1_bat
        if user_team == batting_team:
            self.status = "batting_order"
            self.message = "Set your batting order."
            return
        self.start_innings(batting_team, bowling_team, self.batting_orders[batting_team.name], self.bowling_pools[bowling_team.name])

    def start_second_innings(self):
        """Begin the next innings on autopilot: whichever side is due to bat next (see `next_innings_batting_team`) does so against the other."""
        self._compute_test_target()
        batting_team = self.next_innings_batting_team()
        bowling_team = self.inn1_bowl if batting_team == self.inn1_bat else self.inn1_bat
        self.start_innings(batting_team, bowling_team, self.batting_orders[batting_team.name], self.bowling_pools[bowling_team.name])

    def complete_match(self):
        """Decide the match result from both innings' totals — chase succeeds (win by wickets), chase falls short (win by runs), or scores level triggers a Super Over — then finalize."""
        first = self.innings[0]
        second = self.innings[1]
        if second["runs"] >= first["runs"] + 1:
            winner = self.inn1_bowl
            loser = self.inn1_bat
            margin = wickets_margin(10 - second["wickets"])
        elif first["runs"] > second["runs"]:
            winner = self.inn1_bat
            loser = self.inn1_bowl
            margin = f"won by {first['runs'] - second['runs']} runs"
        else:
            self.setup_super_over()
            return
        self.finalize_match(winner, loser, margin)

    def complete_test_match(self):
        """Decide a Test match's result once play has stopped: a chase that overhauls the target wins by wickets, a side bowled out (or out of overs) short of the target loses by runs, a side bowled out a final time without the other batting again loses by an innings, and anything else (overs/days exhausted mid-chase) is a draw."""
        team_a_innings = [inn for inn in self.innings if inn["team"] == self.inn1_bat]
        team_b_innings = [inn for inn in self.innings if inn["team"] == self.inn1_bowl]
        team_a_runs = sum(inn["runs"] for inn in team_a_innings)
        team_b_runs = sum(inn["runs"] for inn in team_b_innings)
        last = self.innings[-1]
        chasing_team = last["team"]
        defending_team = self.inn1_bowl if chasing_team == self.inn1_bat else self.inn1_bat
        chasing_runs = team_a_runs if chasing_team == self.inn1_bat else team_b_runs
        defending_runs = team_b_runs if chasing_team == self.inn1_bat else team_a_runs

        if chasing_runs > defending_runs:
            margin = wickets_margin(10 - last["wickets"])
            self.finalize_match(chasing_team, defending_team, margin)
            return
        if len(self.innings) == 3 and self.followed_on and not self.match_time_expired():
            # Follow-on enforced and team B's 2nd innings (3rd overall) still
            # fell short of team A's 1st-innings lead — an innings win for
            # team A, no 4th innings needed.
            margin = f"won by an innings and {team_a_runs - team_b_runs} runs"
            self.finalize_match(self.inn1_bat, self.inn1_bowl, margin)
            return
        chasing_all_out = self.innings_is_over() or self.score.get("balls", 0) >= self.format["balls_per_innings"]
        if len(self.innings) == 4 and chasing_all_out and not self.match_time_expired():
            margin = f"won by {defending_runs - chasing_runs} runs"
            self.finalize_match(defending_team, chasing_team, margin)
            return
        # Either the chasing side was bowled out/used its full overs exactly
        # as time ran out, or time ran out with wickets and overs still in
        # hand — either way, no side achieved a winning position in time: a
        # draw, the standard Test outcome for a stopped, undecided match.
        self.finalize_draw()

    def finalize_draw(self):
        """Record a Test match as drawn: no win/loss, a shared point each (1-1, the standard Test points convention), still tallies games-played/form/bowling-bests from whatever innings were completed."""
        self.inn1_bat.points += 1
        self.inn1_bowl.points += 1
        self.inn1_bat.draws += 1
        self.inn1_bowl.draws += 1
        self.finalize_match(None, None, "Match drawn", draw=True)

    def finalize_match(self, winner, loser, margin, draw=False):
        """Record the match result everywhere it needs to land: team W/L and points, every involved player's games-played/team-wins tally, Man of the Match, season bowling-best updates, post-match form adjustments, and the final scorecard appended to the league's match log.

        "Involved" players are derived from every completed innings' batting
        orders and bowlers actually used — not full squads — so bench players
        don't get credited with a game they didn't play. `seen_players`
        prevents double-counting a player across multiple innings or, in
        principle, both teams' involvement sets. When `draw` is set, `winner`/
        `loser` are `None` and win/loss tallies (already applied by
        `finalize_draw`) are skipped, but every other bookkeeping step — stats,
        MOTM, the scorecard — still runs the same way.
        """
        if not draw:
            winner.wins += 1
            winner.points += 2
            loser.losses += 1
        team1, team2 = self.inn1_bat, self.inn1_bowl
        involved_by_team = {team1.name: set(), team2.name: set()}
        for innings in self.innings:
            involved_by_team.setdefault(innings["team"].name, set()).update(innings.get("batting_order", []))
            involved_by_team.setdefault(innings["bowling_team"].name, set()).update(innings.get("bowl_stats", {}).keys())
        seen_players = set()
        win_team_name = winner.name if winner else None
        for team_name, names in involved_by_team.items():
            for name in names:
                player = self.league.find_player_anywhere(name)
                if not player or player.name in seen_players:
                    continue
                ensure_stat_fields(player)
                player.stats["games"] += 1
                if win_team_name and team_name == win_team_name:
                    player.stats["team_wins"] += 1
                seen_players.add(player.name)
        all_bat = {}
        all_bowl = {}
        for innings in self.innings:
            all_bat.update(innings["bat_stats"])
            all_bowl.update(innings["bowl_stats"])
        players = [
            p for name in set().union(*involved_by_team.values())
            for p in [self.league.find_player_anywhere(name)] if p
        ]
        motm_against = winner if winner else team1
        motm = self.league.select_motm(all_bat, all_bowl, players, motm_against)
        ensure_stat_fields(motm)
        motm.stats["motm"] += 1
        for innings in self.innings:
            self.league.update_bowling_bests(self.bowling_pools.get(innings["bowling_team"].name, []), innings["bowl_stats"], innings["team"].name)
            self.engine.eval_match_performances_for_form(
                self.batting_orders.get(innings["team"].name, []),
                self.bowling_pools.get(innings["bowling_team"].name, []),
                innings["bat_stats"],
                innings["bowl_stats"],
            )
        self.card = {
            "round": self.league.round_num,
            "stage": self.stage,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "venue": team_meta(self.team1)["home"],
            "toss": f"{self.toss_winner.name} chose to {self.decision}",
            "winner": winner.name if winner else "",
            "draw": draw,
            "margin": margin,
            "summary": f"{winner.name} {margin}" if winner else margin,
            "motm": motm.name,
            "innings": [self.league.innings_card(inn) for inn in self.innings],
            "impact_subs": list(self.impact_subs),
            "super_over": self.super_over_card(),
        }
        self.league.match_log.append(self.card)
        if not hasattr(self.league, "fixture_results"):
            self.league.fixture_results = []
        self.league.fixture_results.append(self.card)
        self.status = "complete"
        self.message = self.card["summary"]

    def payload(self):
        """Serialise the full live-match state into the JSON dict the frontend renders.

        Includes status/messages, both teams' lineup and scoreboard data,
        context flags telling the UI which panel to show next
        (`lineup_context`/`impact_context`), suggested player picks for
        whatever selection is currently open, and (once available) innings
        cards, the live scoreboard, and the final match card.
        """
        user_team = self.league.user_team()
        innings_payload = []
        for inn in self.innings:
            innings_payload.append(self.league.innings_card(inn))
        suggested_players = self.suggested_roster(self.lineup_context() == "bowling")
        if self.status == "batting_order" and user_team.name in self.xis:
            suggested_players = self.xis[user_team.name]
        lineup_xi, swap_out, swap_in = self.league.resolve_match_xi(user_team, user_team == self.inn1_bat)
        # Present the XI in the user's saved batting order if they have one,
        # otherwise the smart batting order — the SAME order the squad screen
        # shows and a quick-sim plays. resolve_match_xi returns raw selection
        # order (keeper, then batters by rating, then bowlers), so without this
        # the match hub's lineup editor showed a different order than the squad
        # screen until the user saved presets once.
        saved_order = list(getattr(user_team, "saved_batting_order_names", []))
        if saved_order:
            ordered = [n for n in saved_order if n in lineup_xi]
            ordered += [n for n in lineup_xi if n not in ordered]
            lineup_xi = ordered
        else:
            xi_players = [next((p for p in user_team.roster if p.name == n), None) for n in lineup_xi]
            xi_players = [p for p in xi_players if p]
            if len(xi_players) == len(lineup_xi):
                lineup_xi = [p.name for p in self.league.smart_batting_order(xi_players)]
        # At the chase (batting_order) stage the impact sub has already been
        # applied, so the engine's computed batting order is authoritative —
        # the original resolve_match_xi order would put a returning batter at
        # the tail. Use the actual post-sub order so the editor shows (and
        # confirming preserves) the correct lineup.
        if self.status == "batting_order" and user_team.name in self.batting_orders:
            lineup_xi = [p.name for p in self.batting_orders[user_team.name]]
        ipl = getattr(self.league, "competition", "ipl") == "ipl"
        impact_sub_name = (getattr(user_team, "saved_impact_sub_name", "") or self.league.smart_impact_sub(user_team, lineup_xi)) if ipl else ""
        swap_notice = ""
        if ipl and self.lineup_context() == "bowling" and swap_out:
            swap_notice = f"{swap_out} (impact sub) starts in place of {swap_in}. {swap_in} returns at the innings break."
        return {
            "status": self.status,
            "stage": self.stage,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "toss_winner": self.toss_winner.name,
            "decision": self.decision,
            "message": self.message,
            "user_toss": self.status == "toss" and self.toss_winner.name == user_team.name,
            "lineup_context": self.lineup_context(),
            "impact_context": self.impact_context(),
            "suggested": [self.league.player_dict(p) for p in suggested_players],
            "saved_xi": user_team.saved_playing_xi_names,
            "saved_wicketkeeper": getattr(user_team, "saved_wicketkeeper_name", ""),
            "lineup_xi": lineup_xi,
            "impact_sub_name": impact_sub_name,
            "swap_notice": swap_notice,
            "saved_order": user_team.saved_batting_order_names,
            "saved_bowling_order": getattr(user_team, "saved_bowling_over_names", []),
            "score": self.live_score_payload(),
            "available_bowlers": [self.live_bowler_dict(p) for p in self.available_bowlers()],
            "impact": self.impact_payload(),
            "super_over": self.super_over_payload(),
            "innings": innings_payload,
            "card": self.card,
            "match_format": self.match_format,
            "total_balls": self.format["balls_per_innings"],
            "current_day": self.current_day,
            "current_session": self.current_session,
            "sessions_per_day": self.format["sessions_per_day"],
            "overs_remaining_in_session": max(0, self.format["overs_per_session"] - self.overs_bowled_in_session),
            "pending_session_break": self.pending_session_break,
            "follow_on_available": self.status == "follow_on_decision",
            "followed_on": self.followed_on,
            "can_declare": self.format["innings_per_side"] > 1 and self.status == "over" and bool(self.score) and self.score["batting_team"].name == user_team.name,
        }

    def live_bowler_dict(self, player):
        """A player dict (see `LeagueState.player_dict`) augmented with this match's live bowling figures (economy, overs, wickets) for the bowler-selection panel."""
        data = self.score["bowl_stats"].get(player.name, {}) if self.score else {}
        payload = self.league.player_dict(player)
        balls = data.get("balls", 0)
        runs = data.get("runs", 0)
        payload["match_econ"] = round(runs / (balls / 6), 2) if balls else "-"
        payload["match_overs"] = f"{balls // 6}.{balls % 6}"
        payload["match_wickets"] = data.get("wickets", 0)
        return payload

    def lineup_context(self):
        """Which lineup panel the frontend should show: "" (none open), "batting", or "bowling" — based on whether the user's side will bat or bowl in the innings about to start."""
        if self.status not in ("lineup", "batting_order"):
            return ""
        if self.status == "batting_order":
            return "batting"
        user = self.league.user_team()
        if user == self.inn1_bowl:
            return "bowling"
        return "batting"

    def impact_context(self):
        """Which Impact Player sub flow applies at the innings break: "bat_to_bowl" (the user just batted and may swap in a bowler) or "bowl_to_bat" (vice versa), or "" if no sub window is open."""
        if self.status != "impact":
            return ""
        user = self.league.user_team()
        just_batted = self.score["batting_team"] if self.score else self.inn1_bat
        return "bat_to_bowl" if user == just_batted else "bowl_to_bat"

    def live_score_payload(self):
        """The full live-scoreboard JSON for the active innings: scoreline, target, both batters and bowler on strike, partnership, current over, and recent over history — or `None` if no innings is in progress."""
        if not self.score:
            return None
        order = self.score["batting_order"]
        striker = order[min(self.score["striker_idx"], len(order) - 1)] if order else None
        non_striker = order[min(self.score["non_striker_idx"], len(order) - 1)] if order else striker
        striker_name = striker.name if striker else ""
        non_striker_name = non_striker.name if non_striker else ""
        return {
            "scoreline": self.scoreline(),
            "runs": self.score["runs"],
            "wickets": self.score["wickets"],
            "balls": self.score["balls"],
            "target": self.target,
            "batting_team": self.score["batting_team"].name,
            "bowling_team": self.score["bowling_team"].name,
            "batting_team_color": team_meta(self.score["batting_team"])["primary"],
            "bowling_team_color": team_meta(self.score["bowling_team"])["primary"],
            "user_bowling": self.score["bowling_team"].name == self.league.user_team_name,
            "user_batting": self.score["batting_team"].name == self.league.user_team_name,
            "striker": striker_name,
            "non_striker": non_striker_name,
            "partnership": f"{self.score['partnership_runs']} off {self.score['partnership_balls']}",
            "phase": innings_phase(self.score["balls"] // 6, self.format["phase_boundaries"]),
            "active_bowler": self.score["active_bowler"].name if self.score.get("active_bowler") else "",
            "pending_next_batter": self.score.get("pending_next_batter", False),
            "striker_aggression": self.score["batting_aggression"].get(striker_name, 3),
            "non_striker_aggression": self.score["batting_aggression"].get(non_striker_name, 3),
            "bowler_aggression": self.score["bowling_aggression"].get(self.score["active_bowler"].name, 2) if self.score.get("active_bowler") else 2,
            "current_over": self.score.get("current_over_events", []),
            "next_batter_options": [self.league.player_dict(p) for p in self.score["batting_order"][self.score["striker_idx"]:] if self.score.get("pending_next_batter")],
            "last_wicket": self.score.get("current_over_events", [])[-1] if self.score.get("current_over_events", []) and self.score.get("current_over_events", [])[-1].get("kind") == "wicket" else None,
            "bat_stats": [{"name": n, "dismissal": self.score.get("dismissals", {}).get(n, ""), **d} for n, d in self.score["bat_stats"].items()],
            "bowl_stats": [{"name": n, **d, "overs": f"{d['balls'] // 6}.{d['balls'] % 6}", "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0} for n, d in self.score["bowl_stats"].items()],
            "over_log": list(self.score["over_log"]),
        }

    def impact_payload(self):
        """Impact Player sub options at the innings break: the user's current XI and bench, plus the default swap pairing (`default_out`/`default_in`) to preselect, or `None` if it's not currently the break."""
        if self.status != "impact":
            return None
        user = self.league.user_team()
        xi = self.xis[user.name]
        bench = [p for p in user.roster if p not in xi]
        default_out, default_in = self.pending_swaps.get(user.name, ("", ""))
        return {
            "xi": [self.league.player_dict(p) for p in xi],
            "bench": [self.league.player_dict(p) for p in bench],
            "default_out": default_out or "",
            "default_in": default_in or "",
        }

    def super_over_payload(self):
        """Super Over selection JSON for the user (sorted batting/bowling options from their XI) while setup is open, or just the result card once it's resolved."""
        if self.status != "super_over_setup" or not self.super_over:
            return self.super_over_card()
        user = self.league.user_team()
        xi = self.xis.get(user.name, [])
        return {
            "message": self.super_over["message"],
            "batting_first": self.super_over["batting_first"].name,
            "batting_second": self.super_over["batting_second"].name,
            "batters": [self.league.player_dict(p) for p in sorted(xi, key=lambda p: p.current_batting, reverse=True)],
            "bowlers": [self.league.player_dict(p) for p in sorted([p for p in xi if is_bowling_role(p)], key=lambda p: p.current_bowling, reverse=True)],
            "innings": self.super_over.get("innings", []),
            "winner": self.super_over.get("winner", ""),
        }

    def super_over_card(self):
        """Compact, JSON-serialisable Super Over result summary for the match scorecard, or `None` if no Super Over was played."""
        if not self.super_over:
            return None
        return {
            "batting_first": self.super_over["batting_first"].name,
            "batting_second": self.super_over["batting_second"].name,
            "innings": list(self.super_over.get("innings", [])),
            "winner": self.super_over.get("winner", ""),
            "message": self.super_over.get("message", ""),
        }


