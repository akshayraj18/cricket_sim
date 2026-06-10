# models.py
"""Domain model for the IPL franchise sim: individual players and teams.

`Player` tracks a cricketer's static attributes (role, ratings, batting/
bowling profile) plus dynamic state (form, current-match intent, season
stats), and exposes `current_*` properties that blend base rating with form.
`Team` tracks a franchise's roster, leadership, season results, and the
saved lineup/order preferences the UI carries over between matches.
"""
import random

# Mean real-world IPL batting position (2021-2025 ball-by-ball data) for each
# (role, batting_archetype) combination — e.g. a Wicketkeeper "Aggressor" like
# Buttler or de Kock overwhelmingly opens (~1.7), while a Batsman "Finisher"
# like David Miller walks in around #5-6. Used to give freshly-created players
# a realistic natural batting slot instead of relying on archetype labels alone,
# which (e.g. "Spin Specialist" keepers who are actually finishers) don't map
# cleanly to where a player actually bats.
ARCHETYPE_BATTING_POSITION = {
    # #1 — pure openers
    ("Batsman", "Aggressive Opener"): 1.3,
    ("All-Rounder", "Aggressive Opener"): 1.8,
    # #2 — WK openers and attacking #2s
    ("Wicketkeeper", "Aggressive Opener"): 2.0,
    # #3 — classic attacking #3 (not a defensive anchor, not a finisher)
    ("Batsman", "Aggressor"): 3.0,
    ("Wicketkeeper", "Aggressor"): 3.2,
    ("All-Rounder", "Aggressor"): 3.4,
    # #3 — classical anchor
    ("Batsman", "Anchor"): 3.0,
    ("Wicketkeeper", "Anchor"): 3.4,
    # #4 — all-rounder anchors and batting-first all-rounders
    ("All-Rounder", "Anchor"): 4.0,
    # #5 — middle-over utility: rotate, accumulate, bowl a few overs
    ("Batsman", "Middle-over Rotator"): 5.2,
    ("Wicketkeeper", "Middle-over Rotator"): 5.0,
    ("All-Rounder", "Middle-over Rotator"): 5.5,
    ("Bowler (Spin)", "Aggressor"): 5.2,
    ("Bowler (Fast)", "Aggressor"): 5.4,
    # #6 — bowling all-rounder floaters and spin specialist batters
    ("Bowler (Spin)", "Middle-over Rotator"): 6.0,
    ("Bowler (Fast)", "Middle-over Rotator"): 6.2,
    # #7 — finishers: come in to accelerate and hit sixes
    ("Batsman", "Finisher"): 6.6,
    ("All-Rounder", "Finisher"): 6.8,
    ("Wicketkeeper", "Finisher"): 7.0,
    # #8 — lower-order hitters and tail-end bowlers who can bat
    ("Wicketkeeper", "Lower-order Hitter"): 7.6,
    ("Batsman", "Lower-order Hitter"): 7.8,
    ("All-Rounder", "Lower-order Hitter"): 8.0,
    ("Bowler (Spin)", "Finisher"): 8.2,
    ("Bowler (Fast)", "Finisher"): 8.4,
    # #9 — bowling pinch hitters
    ("Bowler (Spin)", "Lower-order Hitter"): 8.6,
    ("Batsman", "Defensive Tailender"): 9.2,
    # #10 — bowling specialists who scratch a run
    ("Wicketkeeper", "Defensive Tailender"): 9.6,
    ("All-Rounder", "Defensive Tailender"): 9.7,
    ("Bowler (Fast)", "Lower-order Hitter"): 9.8,
    ("Bowler (Spin)", "Defensive Tailender"): 10.1,
    # #11 — last man in
    ("Bowler (Fast)", "Defensive Tailender"): 10.7,
}
DEFAULT_BATTING_POSITION_BY_ROLE = {
    "Batsman": 4.0, "Wicketkeeper": 4.0, "All-Rounder": 5.0,
    "Bowler (Fast)": 8.5, "Bowler (Spin)": 8.0,
}


def derive_preferred_position(role, batting_archetype, batting_ovr=None, bowling_ovr=None):
    """Estimate where a player naturally bats (1-11), from real-world IPL position tendencies for their role/archetype.

    Looks up the (role, archetype) pair in `ARCHETYPE_BATTING_POSITION` (built
    from 2021-2025 ball-by-ball IPL data) and rounds its mean position to the
    nearest slot, falling back to a per-role default for unrecognised
    combinations. All-rounders get a small nudge toward the top order when
    their batting clearly outweighs their bowling (and vice versa), so a
    batting-first all-rounder slots higher than a bowling-first one with the
    same archetype label.
    """
    base = ARCHETYPE_BATTING_POSITION.get((role, batting_archetype))
    if base is None:
        base = DEFAULT_BATTING_POSITION_BY_ROLE.get(role, 6.0)
    if role == "All-Rounder" and batting_ovr is not None and bowling_ovr is not None:
        if batting_ovr - bowling_ovr >= 15:
            base -= 1.0
        elif bowling_ovr - batting_ovr >= 15:
            base += 1.0
    return max(1, min(11, round(base)))


class Player:
    """A single cricketer: ratings, profile, in-match state, and season stats.

    `base_ovr`/`batting_ovr`/`bowling_ovr` are the player's stable ratings;
    `current_batting`/`current_bowling`/`current_ovr` blend them with the
    player's `form` to produce the rating actually used in simulation.
    `batting_archetype`, `bowling_phase`, `bowling_type`, `strengths`, and
    `weaknesses` describe tendencies the match engine uses to bias outcomes.
    """

    def __init__(self, name, role, base_ovr, batting_ovr, bowling_ovr, is_overseas, age, batting_hand="Right", bowling_hand="Right", batting_archetype="Strike Rotator", bowling_phase="Flexible", bowling_type="None", strengths="", weaknesses=""):
        self.name = name
        self.role = role
        self.base_ovr = base_ovr
        self.batting_ovr = batting_ovr
        self.bowling_ovr = bowling_ovr
        self.is_overseas = is_overseas
        self.age = age
        self.batting_hand = batting_hand
        self.bowling_hand = bowling_hand
        self.batting_archetype = batting_archetype
        self.bowling_phase = bowling_phase
        self.bowling_type = bowling_type
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.preferred_position = derive_preferred_position(role, batting_archetype, batting_ovr, bowling_ovr)
        self.form = 5
        self.intent = "Normal"
        self.team_name = "Unassigned"
        self.reset_stats()

    def reset_stats(self):
        """Zero out this player's season statistics (used at the start of each new season)."""
        self.stats = {
            "runs": 0, "balls_faced": 0, "outs": 0, "highest_score": 0,
            "fours": 0, "sixes": 0, "fifties": 0, "hundreds": 0,
            "wickets": 0, "runs_conceded": 0, "balls_bowled": 0,
            "maidens": 0, "motm": 0, "best_bowling_wickets": 0,
            "best_bowling_runs": 999,
            "catches": 0, "stumpings": 0, "runouts": 0
        }

    @property
    def form_impact(self):
        """Confidence modifier derived from form (range -4 to +5).

        Form lives on a 1-10 scale with 5 as neutral; this keeps it acting
        as a small swing on top of the player's base ratings rather than a
        wholesale rewrite, so match results stay believable across a season.
        """
        return self.form - 5

    @property
    def current_batting(self):
        """Effective batting rating (1-100): base rating shifted by form."""
        return max(1, min(100, int(self.batting_ovr + self.form_impact)))

    @property
    def current_bowling(self):
        """Effective bowling rating (1-100): base rating shifted by form."""
        return max(1, min(100, int(self.bowling_ovr + self.form_impact)))

    @property
    def current_ovr(self):
        """Effective overall rating (1-100): best of base/batting/bowling, shifted by form."""
        return max(1, min(100, int(max(self.base_ovr, self.batting_ovr, self.bowling_ovr) + self.form_impact)))

    @property
    def batting_strike_rate(self):
        """Season strike rate (runs per 100 balls faced), or 0.0 if yet to bat."""
        if self.stats["balls_faced"] == 0: return 0.0
        return (self.stats["runs"] / self.stats["balls_faced"]) * 100

    @property
    def bowling_economy(self):
        """Season bowling economy (runs conceded per over), or 0.0 if yet to bowl."""
        if self.stats["balls_bowled"] == 0: return 0.0
        return (self.stats["runs_conceded"] / (self.stats["balls_bowled"] / 6))

    def apply_game_performance_on_form(self, specialized_impact):
        """Nudge form up or down after a match, scaled by age.

        `specialized_impact` is a small signed value (e.g. +1 for a strong
        knock, -1 for a poor one) from `MatchEngine.eval_match_performances_for_form`.
        Younger players (<=23) swing more in both directions (development/
        inconsistency), older players (>=35) swing less on the upside and
        recover more slowly on the downside, modelling experience and decline.
        Form is clamped to the 1-10 scale.
        """
        if specialized_impact > 0:
            if self.age <= 23:
                adjusted = specialized_impact + 0.35
            elif self.age <= 28:
                adjusted = specialized_impact + 0.15
            elif self.age >= 35:
                adjusted = specialized_impact * 0.65
            else:
                adjusted = specialized_impact
        else:
            if self.age <= 23:
                adjusted = specialized_impact * 1.20
            elif self.age >= 35:
                adjusted = specialized_impact * 0.70
            else:
                adjusted = specialized_impact
        self.form = max(1, min(10, self.form + adjusted))

    def apply_offseason_progression(self):
        """Age the player up by a year and randomly grow or decline their ratings.

        Growth is sampled from an age-banded weighted distribution: young
        players (<=21) skew toward solid gains, players in their late 20s to
        early 30s mostly plateau or dip slightly, and players over 34 tend to
        decline. The same delta is applied to both batting and bowling
        ratings, `base_ovr` is recomputed as their max, and form resets to
        neutral for the new season.
        """
        if self.age <= 21:
            growth = random.choices([1, 2, 3, 4, 5], weights=[1, 3, 4, 3, 1])[0]
        elif self.age <= 25:
            growth = random.choices([0, 1, 2, 3, 4], weights=[1, 3, 4, 2, 1])[0]
        elif self.age <= 30:
            growth = random.choices([-1, 0, 1, 2], weights=[1, 3, 3, 1])[0]
        elif self.age <= 34:
            growth = random.choices([-2, -1, 0, 1], weights=[2, 3, 2, 1])[0]
        else:
            growth = random.choices([-5, -4, -3, -2, -1], weights=[1, 2, 3, 3, 1])[0]
        self.batting_ovr = max(1, min(100, self.batting_ovr + growth))
        self.bowling_ovr = max(1, min(100, self.bowling_ovr + growth))
        self.base_ovr = max(self.batting_ovr, self.bowling_ovr)
        self.age += 1
        self.form = 5


class Team:
    """An IPL franchise: roster, leadership, season results, and saved UI preferences.

    The `saved_*` fields cache the user's last lineup, batting/bowling order,
    keeper choice, and impact-sub plan so the web UI can offer to carry them
    over into the next match without the user re-entering them.
    """

    def __init__(self, name):
        self.name = name
        self.roster = []
        self.points = 0
        self.wins = 0
        self.losses = 0
        self.runs_scored = 0
        self.balls_faced = 0
        self.runs_conceded = 0
        self.balls_bowled = 0
        self.captain = None
        self.vice_captain = None
        self.saved_playing_xi_names = []
        self.saved_batting_first_xi_names = []
        self.saved_bowling_first_xi_names = []
        self.saved_bat_to_bowl_sub = {"out": "", "in": ""}
        self.saved_bowl_to_bat_sub = {"out": "", "in": ""}
        self.saved_wicketkeeper_name = ""
        self.saved_batting_order_names = []
        self.saved_bowling_over_names = []

    @property
    def games_played(self):
        """Total matches completed this season (wins plus losses)."""
        return self.wins + self.losses

    @property
    def net_run_rate(self):
        """Standard cricket NRR: (runs scored per over faced) minus (runs conceded per over bowled).

        Falls back to 1.0 overs for either side of the ratio when the team
        hasn't batted/bowled yet, avoiding a division by zero before a season starts.
        """
        overs_faced = self.balls_faced / 6 if self.balls_faced > 0 else 1.0
        overs_bowled = self.balls_bowled / 6 if self.balls_bowled > 0 else 1.0
        return (self.runs_scored / overs_faced) - (self.runs_conceded / overs_bowled)

    def auto_assign_cpu_leadership(self):
        """Hand the captaincy and vice-captaincy to the two highest-rated squad members."""
        sorted_r = sorted(self.roster, key=lambda p: p.current_ovr, reverse=True)
        self.captain = sorted_r[0]
        self.vice_captain = sorted_r[1]

