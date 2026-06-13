"""Single-match driver: toss, lineups, over-by-over simulation, and scorecards.

`LiveMatch` owns everything about one match end-to-end, calling into
`MatchEngine` purely for per-ball outcome sampling while it manages the
state machine (`status`), lineups/orders/bowling plans, the live scoreboard,
super overs, impact substitutions, and the final scorecard payload.
"""
import random

from cricket_sim_engine.engine import MatchEngine
from cricket_sim_engine.sim.constants import TEAM_META
from cricket_sim_engine.sim.helpers import (
    ensure_stat_fields,
    innings_phase,
    is_batting_role,
    is_bowling_role,
    is_wicketkeeper_option,
    counts_as_batter,
    counts_as_bowler,
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
        self.engine = MatchEngine(league.user_team_name, getattr(league, "difficulty", "hard"))
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
                order = [p for p in xi if p.name in saved_order]
                order.sort(key=lambda p: saved_order.index(p.name))
                order += [p for p in xi if p not in order]
                self.batting_orders[team.name] = order if len(order) == 11 else self.league.smart_batting_order(xi)
                self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
                self.wicketkeepers.setdefault(team.name, self.default_keeper(team, xi))
                if team.name == self.league.user_team_name:
                    self.set_bowling_plan(team, getattr(team, "saved_bowling_over_names", []))
        self.start_first_innings_if_ready()
        if self.status == "batting_order" and self.league.user_team().name in self.xis:
            self.start_second_innings()
        while self.status == "next_batter" and self.score and self.score.get("pending_next_batter"):
            order = self.score["batting_order"]
            idx = self.score["striker_idx"]
            self.select_next_batter(order[idx].name)
            while self.status == "over":
                self.play_over(auto=True)
        while self.status == "over":
            self.play_over(auto=True)
        if self.status == "impact":
            user_team = self.league.user_team()
            swap_out, swap_in = self.pending_swaps.get(user_team.name, (None, None))
            self.apply_impact_sub(out_name=swap_out, in_name=swap_in, auto=True)
        while self.status == "over":
            self.play_over(auto=True)
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
        """Store a pre-planned 20-over bowling order for `team` if `names` forms a valid one (20 entries, each bowler appearing at most 4 times — the IPL per-bowler over cap); otherwise clear the plan and fall back to per-over bowler selection."""
        valid = [p.name for p in self.bowling_pools.get(team.name, [])]
        clean = [name for name in names if name in valid]
        if len(clean) == 20 and all(clean.count(name) <= 4 for name in set(clean)):
            self.bowling_plan_for[team.name] = clean
        else:
            self.bowling_plan_for[team.name] = []

    def start_first_innings_if_ready(self):
        """Once both teams have a confirmed XI, begin the first innings."""
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
            "batting_aggression": {p.name: 3 for p in batting_order},
            "bowling_aggression": {p.name: 2 for p in bowling_pool},
            "pending_next_batter": False,
        }
        self.status = "over"
        self.message = f"{batting_team.name} innings started. Pick the next bowler."

    def available_bowlers(self):
        """Bowlers eligible to bowl the next over, best phase-fit first.

        Excludes anyone who has already bowled their 4-over IPL allowance and
        (when possible) whoever bowled the previous over, since the same
        bowler can't deliver consecutive overs. Falls back to progressively
        looser pools (allow the previous bowler, then allow capped bowlers)
        if no one else is left — keeps the match playable in edge cases like
        a side carrying very few specialist bowlers.
        """
        if self.status != "over" or not self.score:
            return []
        tracked = self.score["overs_tracked"]
        last = self.score["last_bowler"]
        options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < 4 and p != last]
        if not options:
            options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < 4]
        if not options:
            options = list(self.score["bowling_pool"])
        phase = innings_phase(self.score["balls"] // 6)
        return sorted(options, key=lambda p: self.bowler_phase_score(p, phase), reverse=True)

    def cpu_bowler(self):
        """The CPU's choice of next bowler: simply the best phase-fit option from `available_bowlers`."""
        return self.available_bowlers()[0]

    def bowler_phase_score(self, player, phase):
        """Heuristic score for how well this bowler suits the given match phase, used to rank/select CPU bowling options.

        Starts from the bowler's rating and adds bonuses for matching their
        specialised `bowling_phase`, and for pace/swing in the powerplay or
        death, spin in the middle overs, and variations at the death.
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

        self.score["last_bowler"] = bowler
        self.score["overs_tracked"][bowler.name] = self.score["overs_tracked"].get(bowler.name, 0) + 1
        self.score["active_bowler"] = bowler
        self.score["current_over_events"] = []
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
        end_ball = min(((start_balls // 6) + 1) * 6, start_balls + max_balls, 120)
        self.score["last_event_wicket"] = False
        while self.score["balls"] < end_ball and not self.innings_is_over():
            if self.target and self.score["runs"] >= self.target:
                break
            event = self.play_ball(bowler)
            self.score["current_over_events"].append(event)
            self.score["last_event_wicket"] = event["kind"] == "wicket"
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name and self.score["wickets"] < 10 and self.score["balls"] < 120:
                self.score["pending_next_batter"] = True
                self.status = "next_batter"
                self.message = f"{event['description']}. Choose who comes in next."
                return
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name:
                break

        if self.score["balls"] % 6 == 0 or self.score["balls"] >= 120 or self.innings_is_over() or (self.target and self.score["runs"] >= self.target):
            self.close_current_over()

        if self.score["balls"] >= 120 or self.innings_is_over() or (self.target and self.score["runs"] >= self.target):
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
        phase = innings_phase(over_num)
        striker.match_phase = phase
        bowler.match_phase = phase
        striker.batting_aggression = self.score["batting_aggression"].get(striker.name, 3)
        bowler.bowling_aggression = self.score["bowling_aggression"].get(bowler.name, 2)
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
        """Short human-readable score string, e.g. "Mumbai Indians 142/3 (15.2)"."""
        overs = f"{self.score['balls'] // 6}.{self.score['balls'] % 6}"
        return f"{self.score['batting_team'].name} {self.score['runs']}/{self.score['wickets']} ({overs})"

    def finish_innings(self):
        """Close out the current innings: roll up career milestones (highest score, fifties/hundreds), update both teams' season run/ball totals (for NRR), archive the innings card, and either set the chase target and move to the second innings or complete the match.

        All-out innings count as a full 120 balls faced for NRR purposes
        (the standard cricket convention — a side bowled out is treated as
        having "used" its full quota).
        """
        batting_team = self.score["batting_team"]
        bowling_team = self.score["bowling_team"]
        runs = self.score["runs"]
        wickets = self.score["wickets"]
        balls = self.score["balls"]
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
        final_balls = 120 if wickets == 10 else balls
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
        if self.current_innings == 1:
            self.current_innings = 2
            self.target = runs + 1
            self.status = "impact"
            self.message = f"Innings break. Target is {self.target}. Use one Impact Player sub if you want."
        else:
            self.complete_match()

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

    def prepare_second_innings(self):
        """Move to the second innings: if the user is chasing, pause for them to set a batting order first; otherwise start the innings immediately."""
        user_team = self.league.user_team()
        if user_team == self.inn1_bowl:
            self.status = "batting_order"
            self.message = "Set your batting order for the chase."
            return
        self.start_innings(self.inn1_bowl, self.inn1_bat, self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name])

    def start_second_innings(self):
        """Begin the chase: the side that bowled first now bats against the target."""
        self.start_innings(self.inn1_bowl, self.inn1_bat, self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name])

    def complete_match(self):
        """Decide the match result from both innings' totals — chase succeeds (win by wickets), chase falls short (win by runs), or scores level triggers a Super Over — then finalize."""
        first = self.innings[0]
        second = self.innings[1]
        if second["runs"] >= first["runs"] + 1:
            winner = self.inn1_bowl
            loser = self.inn1_bat
            margin = f"won by {10 - second['wickets']} wickets"
        elif first["runs"] > second["runs"]:
            winner = self.inn1_bat
            loser = self.inn1_bowl
            margin = f"won by {first['runs'] - second['runs']} runs"
        else:
            self.setup_super_over()
            return
        self.finalize_match(winner, loser, margin)

    def finalize_match(self, winner, loser, margin):
        """Record the match result everywhere it needs to land: team W/L and points, every involved player's games-played/team-wins tally, Man of the Match, season bowling-best updates, post-match form adjustments, and the final scorecard appended to the league's match log.

        "Involved" players are derived from both innings' batting orders and
        bowlers actually used — not full squads — so bench players don't get
        credited with a game they didn't play. `seen_players` prevents
        double-counting a player who, in principle, could appear in both
        teams' involvement sets.
        """
        first = self.innings[0]
        second = self.innings[1]
        winner.wins += 1
        winner.points += 2
        loser.losses += 1
        involved_by_team = {winner.name: set(), loser.name: set()}
        for innings in (first, second):
            involved_by_team.setdefault(innings["team"].name, set()).update(innings.get("batting_order", []))
            involved_by_team.setdefault(innings["bowling_team"].name, set()).update(innings.get("bowl_stats", {}).keys())
        seen_players = set()
        for name in involved_by_team.get(winner.name, set()):
            player = self.league.find_player_anywhere(name)
            if not player:
                continue
            ensure_stat_fields(player)
            player.stats["games"] += 1
            player.stats["team_wins"] += 1
            seen_players.add(player.name)
        for name in involved_by_team.get(loser.name, set()):
            player = self.league.find_player_anywhere(name)
            if not player:
                continue
            ensure_stat_fields(player)
            if player.name not in seen_players:
                player.stats["games"] += 1
        all_bat = {**first["bat_stats"], **second["bat_stats"]}
        all_bowl = {**first["bowl_stats"], **second["bowl_stats"]}
        players = [
            p for name in set().union(*involved_by_team.values())
            for p in [self.league.find_player_anywhere(name)] if p
        ]
        motm = self.league.select_motm(all_bat, all_bowl, players, winner)
        ensure_stat_fields(motm)
        motm.stats["motm"] += 1
        self.league.update_bowling_bests(self.bowling_pools[self.inn1_bowl.name], first["bowl_stats"], self.inn1_bat.name)
        self.league.update_bowling_bests(self.bowling_pools[self.inn1_bat.name], second["bowl_stats"], self.inn1_bowl.name)
        self.engine.eval_match_performances_for_form(self.batting_orders[self.inn1_bat.name], self.bowling_pools[self.inn1_bowl.name], first["bat_stats"], first["bowl_stats"])
        self.engine.eval_match_performances_for_form(self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name], second["bat_stats"], second["bowl_stats"])
        self.card = {
            "round": self.league.round_num,
            "stage": self.stage,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "venue": TEAM_META[self.team1.name]["home"],
            "toss": f"{self.toss_winner.name} chose to {self.decision}",
            "winner": winner.name,
            "margin": margin,
            "summary": f"{winner.name} {margin}",
            "motm": motm.name,
            "innings": [self.league.innings_card(first), self.league.innings_card(second)],
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
        # At the chase (batting_order) stage the impact sub has already been
        # applied, so the engine's computed batting order is authoritative —
        # the original resolve_match_xi order would put a returning batter at
        # the tail. Use the actual post-sub order so the editor shows (and
        # confirming preserves) the correct lineup.
        if self.status == "batting_order" and user_team.name in self.batting_orders:
            lineup_xi = [p.name for p in self.batting_orders[user_team.name]]
        impact_sub_name = getattr(user_team, "saved_impact_sub_name", "") or self.league.smart_impact_sub(user_team, lineup_xi)
        swap_notice = ""
        if self.lineup_context() == "bowling":
            swap_notice = f"{swap_out} (impact sub) starts in place of {swap_in} — {swap_in} returns at the innings break."
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
        return "bat_to_bowl" if user == self.inn1_bat else "bowl_to_bat"

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
            "user_bowling": self.score["bowling_team"].name == self.league.user_team_name,
            "user_batting": self.score["batting_team"].name == self.league.user_team_name,
            "striker": striker_name,
            "non_striker": non_striker_name,
            "partnership": f"{self.score['partnership_runs']} off {self.score['partnership_balls']}",
            "phase": innings_phase(self.score["balls"] // 6),
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
            "over_log": self.score["over_log"][-6:],
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


