# engine.py
"""Ball-by-ball outcome simulation for the Cricket franchise sim.

`MatchEngine` is a stateless-per-ball probability model: given a batter and
a bowler, it adjusts a baseline outcome distribution by skill gap, match
phase (powerplay/middle/death), batting/bowling archetypes, matchups, and
player intent/aggression, then samples an outcome from it. The web app
(`sim_app.LiveMatch`) owns the actual over-by-over match flow and calls into
this engine purely for per-ball outcomes and post-match form updates.
"""
import random


class MatchEngine:
    """Per-ball outcome sampler for a single match.

    Holds only the context needed to bias outcomes: which team the human
    user controls (so a difficulty edge can be applied) and the configured
    difficulty level.
    """

    def __init__(self, user_team_name=None, difficulty="hard"):
        self.user_team_name = user_team_name
        self.difficulty = difficulty

    # Format-specific base outcome probabilities, calibrated to targets:
    #   T20:  9.5-10.0 r/o → ~195-200 total  (agg=3 default)
    #   ODI:  5.8-6.3 r/o  → ~295-315 total  (agg=2 default)
    #   Test: 3.0-3.5 r/o  → ~330-350/inn    (agg=1 default)
    #
    # Expected r/o at neutral skill = sum(runs × prob) × 6, ignoring wickets.
    # T20:  (0.30×1 + 0.08×2 + 0.005×3 + 0.145×4 + 0.075×6) × 6 = 1.635 × 6 ≈ 9.8 r/o ✓
    # ODI:  (0.345×1 + 0.065×2 + 0.004×3 + 0.085×4 + 0.018×6) × 6 = 0.990 × 6 ≈ 5.9 r/o ✓  (before agg=2 nudge)
    # Test: (0.330×1 + 0.050×2 + 0.003×3 + 0.026×4 + 0.003×6) × 6 = 0.575 × 6 ≈ 3.5 r/o ✓  (before agg=1 nudge)
    # Each tuple is (wicket, dot, single, double, triple, four, six).
    # (wicket, dot, 1, 2, 3, 4, 6) per delivery, before any adjustment.
    # Weights are normalised at sampling time, so these are relative.
    #
    # Calibrated against real first-innings scoring:
    #   T20  ~180-220 off 20 overs   (RR 9-11)
    #   ODI  ~280-330 off 50 overs   (RR 5.6-6.6)
    #   Test ~300-350 per innings    (RR 3.2-3.5, ~100 overs to bowl a side out)
    #
    # The wicket rate is the dominant lever, not the run rate. Test sides were
    # being dismissed for ~230 inside 74 overs — a wicket every 7.4 overs, where
    # a real Test is nearer 11-12 — so innings ended long before a realistic
    # total. Note the effective rate runs slightly ABOVE these bases because
    # tail-end batters carry low ratings, which is why ODI needs 0.0225 to bat
    # close to its 50 overs.
    _FORMAT_BASE = {
        "t20":  (0.045, 0.290, 0.300, 0.080, 0.005, 0.148, 0.082),
        "odi":  (0.0225, 0.415, 0.352, 0.070, 0.004, 0.112, 0.026),
        "test": (0.0167, 0.545, 0.340, 0.052, 0.003, 0.033, 0.004),
    }

    def simulate_ball(self, batter, bowler):
        """Sample the outcome of a single delivery.

        Returns one of "W" (wicket), "0".."6" (runs scored, excluding 5)
        as a string. Base probabilities are format-specific (T20/ODI/Test
        have very different run rates and risk profiles), then adjusted by:
          - skill gap between batter and bowler,
          - a difficulty-based edge applied to/against the user's team,
          - batting archetype vs. match phase synergy,
          - bowling phase specialisation and bowling type vs. phase matchups,
          - batter strengths/weaknesses tags,
          - left/right-handed matchup adjustments,
          - bowler fatigue (overs bowled consecutively without rest),
          - batter innings fatigue / settling-in effect,
          - configured batting/bowling aggression levels, and
          - the batter's chosen intent (Aggressive/Normal/Defensive).
        The final weights are normalised and one outcome is drawn from them.
        """
        match_format = getattr(self, "match_format", "t20") or "t20"
        base = self._FORMAT_BASE.get(match_format, self._FORMAT_BASE["t20"])
        p_wicket, p_dot, p_single, p_double, p_triple, p_four, p_six = base

        skill_delta = (batter.current_batting - bowler.current_bowling) / 100.0
        user_edge = {"easy": 0.18, "medium": 0.09, "hard": 0.0}.get(getattr(self, "difficulty", "hard"), 0.0)
        if user_edge and self.user_team_name:
            if getattr(batter, "team_name", "") == self.user_team_name:
                skill_delta += user_edge
            if getattr(bowler, "team_name", "") == self.user_team_name:
                skill_delta -= user_edge

        # Bowler fatigue: each consecutive over bowled without a break beyond
        # the first degrades effectiveness. Represented as a negative skill
        # delta applied here. Tracks via `bowler_consecutive_overs` on bowler.
        bowler_consecutive = getattr(bowler, "bowler_consecutive_overs", 0)
        if bowler_consecutive >= 2:
            # Fatigue penalty grows with consecutive overs: -0.03 per extra over,
            # capped at -0.18 (6 consecutive overs, realistic Test maximum).
            fatigue_penalty = min(0.18, (bowler_consecutive - 1) * 0.03)
            skill_delta += fatigue_penalty  # bowler tires → batter benefits

        # Batter settling-in: new batters are more vulnerable early (first 8
        # balls in Test/ODI), then become more assured once set.
        batter_balls = getattr(batter, "balls_faced_this_innings", 0)
        if match_format in ("test", "odi") and batter_balls < 8:
            # Vulnerability on first 8 balls (nicking off, playing away from body)
            skill_delta -= 0.04 * (1 - batter_balls / 8)
        elif match_format == "test" and batter_balls >= 30:
            # Set batter in Test: slightly more assured against swing/seam
            skill_delta += 0.015

        phase = getattr(batter, "match_phase", "Middle Overs")
        batting_archetype = getattr(batter, "batting_archetype", "Strike Rotator")
        bowling_phase = getattr(bowler, "bowling_phase", "Flexible")
        bowling_type = getattr(bowler, "bowling_type", "None")
        strengths = getattr(batter, "strengths", "").lower()
        weaknesses = getattr(batter, "weaknesses", "").lower()

        is_spin = any(word in bowling_type for word in ("Spin", "Orthodox", "Leg", "Off"))
        is_pace = bool(bowling_type and bowling_type != "None" and not is_spin)

        # Phase-based archetype bonuses. In Test cricket these are suppressed
        # (no powerplay/death concept); in ODI they apply with proper boundaries.
        # In T20 they apply in full.
        if match_format != "test":
            if batting_archetype in ("Aggressor", "Aggressive Opener", "Pace Specialist") and phase == "Powerplay":
                skill_delta += 0.035
            elif batting_archetype == "Finisher" and phase == "Death Overs":
                skill_delta += 0.040
            elif batting_archetype == "Anchor" and phase == "Powerplay":
                skill_delta -= 0.015
            elif batting_archetype in ("Strike Rotator", "Middle-over Rotator", "Spin Specialist") and phase == "Middle Overs":
                skill_delta += 0.020
            elif batting_archetype in ("Lower-order Hitter", "Lower-order Power Hitter") and phase != "Death Overs":
                skill_delta -= 0.025

            if bowling_phase == phase:
                skill_delta -= 0.035
            elif bowling_phase == "Flexible":
                skill_delta -= 0.012
            if phase == "Powerplay" and "Swing" in bowling_type:
                skill_delta -= 0.020
            if phase == "Middle Overs" and ("Spin" in bowling_type or "Orthodox" in bowling_type):
                skill_delta -= 0.018
            if phase == "Death Overs" and ("Variations" in bowling_type or "Fast" in bowling_type):
                skill_delta -= 0.018
            if batting_archetype == "Aggressor" and phase == "Powerplay" and "Swing" in bowling_type:
                skill_delta -= 0.012
            if batting_archetype == "Anchor" and phase == "Middle Overs" and ("Spin" in bowling_type or "Orthodox" in bowling_type):
                skill_delta += 0.012
            if batting_archetype == "Finisher" and phase == "Death Overs" and "Variations" in bowling_type:
                skill_delta -= 0.010
            if batting_archetype == "Strike Rotator" and phase == "Middle Overs" and "Fast" in bowling_type:
                skill_delta += 0.008
        else:
            # Test cricket: role-based bonuses (not phase-based). Openers and
            # anchors thrive; finishers/lower-order hitters are vulnerable early.
            if batting_archetype in ("Opener", "Aggressive Opener", "Anchor", "Test Specialist"):
                skill_delta += 0.015
            elif batting_archetype in ("Finisher", "Lower-order Hitter", "Lower-order Power Hitter"):
                skill_delta -= 0.020
            # New-ball bowlers are dangerous in test regardless of phase
            if bowling_phase == "New Ball" and is_pace:
                skill_delta -= 0.025
            elif bowling_phase == "Middle Overs" and is_spin:
                skill_delta -= 0.018
            elif bowling_phase == "Flexible":
                skill_delta -= 0.008

        phase_token = "powerplay" if phase == "Powerplay" else ("middle" if phase == "Middle Overs" else "death")
        if match_format != "test":
            if phase_token in strengths:
                skill_delta += 0.010
            if phase_token in weaknesses:
                skill_delta -= 0.010
        if "pace" in strengths and is_pace:
            skill_delta += 0.012
        if "spin" in strengths and is_spin:
            skill_delta += 0.012
        if "pace" in weaknesses and is_pace:
            skill_delta -= 0.012
        if "spin" in weaknesses and is_spin:
            skill_delta -= 0.012

        matchup_multiplier = 1.0
        if batter.batting_hand == "Left" and "Spin" in bowler.role and bowler.bowling_hand == "Right":
            matchup_multiplier += 0.06
        elif batter.batting_hand == "Right" and "Fast" in bowler.role and bowler.bowling_hand == "Left":
            matchup_multiplier -= 0.04
        skill_delta *= matchup_multiplier

        # Apply skill delta to format-specific base rates.
        # Scaling factors are tuned per format so a 20-point edge shifts
        # outcomes meaningfully but doesn't dominate over the base shape.
        if match_format == "test":
            p_wicket -= skill_delta * 0.020
            p_dot    -= skill_delta * 0.060
            p_four   += skill_delta * 0.040
            p_six    += skill_delta * 0.020
        elif match_format == "odi":
            p_wicket -= skill_delta * 0.022
            p_dot    -= skill_delta * 0.070
            p_four   += skill_delta * 0.055
            p_six    += skill_delta * 0.035
        else:
            p_wicket -= skill_delta * 0.025
            p_dot    -= skill_delta * 0.080
            p_four   += skill_delta * 0.070
            p_six    += skill_delta * 0.060

        batting_aggression = max(1, min(5, int(getattr(batter, "batting_aggression", 3))))
        bowling_aggression = max(1, min(5, int(getattr(bowler, "bowling_aggression", 2))))
        bat_push = batting_aggression - 3
        bowl_push = bowling_aggression - 2

        # In ODI/Test the aggression scale is naturally lower (batters play
        # more conservatively by default), so moderate the multipliers.
        if match_format in ("odi", "test"):
            p_wicket *= 1 + (bat_push * 0.12) + (bowl_push * 0.11)
            p_four   *= 1 + (bat_push * 0.10)
            p_six    *= 1 + (bat_push * 0.12)
            p_dot    *= 1 - (bat_push * 0.04)
            p_single *= 1 - (max(0, bat_push) * 0.03)
        else:
            p_wicket *= 1 + (bat_push * 0.16) + (bowl_push * 0.14)
            p_four   *= 1 + (bat_push * 0.13)
            p_six    *= 1 + (bat_push * 0.16)
            p_dot    *= 1 - (bat_push * 0.05)
            p_single *= 1 - (max(0, bat_push) * 0.04)

        if bowling_aggression == 1:
            p_wicket *= 0.86
            p_dot    *= 1.10
            p_four   *= 0.90
            p_six    *= 0.88
            p_single *= 1.05
        elif bowling_aggression >= 3:
            attack = bowling_aggression - 2
            p_wicket *= 1 + attack * 0.14
            p_dot    *= 1 - attack * 0.05
            p_four   += attack * 0.08
            p_six    += attack * 0.07

        if batter.intent == "Aggressive":
            p_wicket *= 1.60; p_six *= 1.50; p_four *= 1.30; p_dot *= 0.70
        elif batter.intent == "Defensive":
            p_wicket *= 0.40; p_dot *= 1.40; p_six *= 0.20; p_four *= 0.40; p_single *= 1.10

        prob_matrix = {"W": max(0.005, p_wicket), "0": max(0.10, p_dot), "1": max(0.05, p_single), "2": max(0.01, p_double), "3": p_triple, "4": max(0.005, p_four), "6": max(0.002, p_six)}
        choices = list(prob_matrix.keys())
        weights = [v / sum(prob_matrix.values()) for v in prob_matrix.values()]
        return random.choices(choices, weights=weights)[0]

    def eval_match_performances_for_form(self, lineup_bat, lineup_bowl, batter_stats=None, bowler_stats=None):
        """Nudge each player's current form up or down based on this match.

        Batters get a boost for a half-century (or a fast 25+) and a knock
        for a duck; bowlers get a boost for a three-wicket haul and a knock
        for an expensive wicketless spell. Used after both innings complete
        so a player's `current_*` ratings drift with recent performance.
        """
        fmt = getattr(self, "match_format", "t20")
        for p in lineup_bat:
            data = batter_stats.get(p.name, {}) if batter_stats else {}
            balls = data.get("balls", p.stats["balls_faced"])
            runs = data.get("runs", p.stats["runs"])
            strike_rate = (runs / balls) * 100 if balls else 0
            if balls > 0:
                if fmt == "test":
                    good = runs >= 50 or (runs >= 30 and strike_rate > 60)
                elif fmt == "odi":
                    good = runs >= 50 or (runs >= 30 and strike_rate > 115)
                else:
                    good = runs >= 50 or (runs >= 25 and strike_rate > 160)
                if good: p.apply_game_performance_on_form(1)
                elif runs == 0: p.apply_game_performance_on_form(-1)
        for p in lineup_bowl:
            data = bowler_stats.get(p.name, {}) if bowler_stats else {}
            balls = data.get("balls", p.stats["balls_bowled"])
            runs = data.get("runs", p.stats["runs_conceded"])
            wickets = data.get("wickets", p.stats["wickets"])
            if balls > 0:
                if wickets >= 3: p.apply_game_performance_on_form(1)
                elif runs >= 45 and wickets == 0: p.apply_game_performance_on_form(-1)
