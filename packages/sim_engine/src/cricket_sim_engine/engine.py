# engine.py
"""Ball-by-ball outcome simulation for the IPL franchise sim.

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

    def simulate_ball(self, batter, bowler):
        """Sample the outcome of a single delivery.

        Returns one of "W" (wicket), "0".."6" (runs scored, excluding 5)
        as a string. The base probabilities are derived from the gap between
        the batter's batting rating and the bowler's bowling rating
        (`skill_delta`), then nudged by:
          - a difficulty-based edge applied to/against the user's team,
          - batting archetype vs. match phase synergy (e.g. Finishers thrive
            in death overs, Anchors are cautious in the powerplay),
          - bowling phase specialisation and bowling type vs. phase matchups,
          - the batter's strengths/weaknesses tags against phase and
            pace/spin,
          - left/right-handed matchup adjustments,
          - configured batting/bowling aggression levels, and
          - the batter's chosen intent (Aggressive/Normal/Defensive).
        The final weights are normalised and one outcome is drawn from them.
        """
        skill_delta = (batter.current_batting - bowler.current_bowling) / 100.0
        user_edge = {"easy": 0.18, "medium": 0.09, "hard": 0.0}.get(getattr(self, "difficulty", "hard"), 0.0)
        if user_edge and self.user_team_name:
            if getattr(batter, "team_name", "") == self.user_team_name:
                skill_delta += user_edge
            if getattr(bowler, "team_name", "") == self.user_team_name:
                skill_delta -= user_edge
        phase = getattr(batter, "match_phase", "Middle Overs")
        batting_archetype = getattr(batter, "batting_archetype", "Strike Rotator")
        bowling_phase = getattr(bowler, "bowling_phase", "Flexible")
        bowling_type = getattr(bowler, "bowling_type", "None")
        strengths = getattr(batter, "strengths", "").lower()
        weaknesses = getattr(batter, "weaknesses", "").lower()

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
        is_spin = any(word in bowling_type for word in ("Spin", "Orthodox", "Leg", "Off"))
        is_pace = bool(bowling_type and bowling_type != "None" and not is_spin)
        phase_token = "powerplay" if phase == "Powerplay" else ("middle" if phase == "Middle Overs" else "death")
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

        p_wicket = 0.045 - (skill_delta * 0.025)
        p_dot = 0.360 - (skill_delta * 0.080)
        p_single, p_double, p_triple = 0.350, 0.070, 0.005
        p_four = 0.120 + (skill_delta * 0.070)
        p_six = 0.050 + (skill_delta * 0.060)

        batting_aggression = max(1, min(5, int(getattr(batter, "batting_aggression", 3))))
        bowling_aggression = max(1, min(5, int(getattr(bowler, "bowling_aggression", 2))))
        bat_push = batting_aggression - 3
        bowl_push = bowling_aggression - 2

        p_wicket *= 1 + (bat_push * 0.16) + (bowl_push * 0.14)
        p_four *= 1 + (bat_push * 0.13)
        p_six *= 1 + (bat_push * 0.16)
        p_dot *= 1 - (bat_push * 0.05)
        p_single *= 1 - (max(0, bat_push) * 0.04)
        if bowling_aggression == 1:
            p_wicket *= 0.86
            p_dot *= 1.10
            p_four *= 0.90
            p_six *= 0.88
            p_single *= 1.05
        elif bowling_aggression >= 3:
            attack = bowling_aggression - 2
            p_wicket *= 1 + attack * 0.14
            p_dot *= 1 - attack * 0.05
            p_four *= 1 + attack * 0.08
            p_six *= 1 + attack * 0.07

        if batter.intent == "Aggressive":
            p_wicket *= 1.60; p_six *= 1.50; p_four *= 1.30; p_dot *= 0.70
        elif batter.intent == "Defensive":
            p_wicket *= 0.40; p_dot *= 1.40; p_six *= 0.20; p_four *= 0.40; p_single *= 1.10

        prob_matrix = {"W": max(0.005, p_wicket), "0": max(0.10, p_dot), "1": max(0.05, p_single), "2": max(0.01, p_double), "3": p_triple, "4": max(0.02, p_four), "6": max(0.01, p_six)}
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
        for p in lineup_bat:
            data = batter_stats.get(p.name, {}) if batter_stats else {}
            balls = data.get("balls", p.stats["balls_faced"])
            runs = data.get("runs", p.stats["runs"])
            strike_rate = (runs / balls) * 100 if balls else 0
            if balls > 0:
                if runs >= 50 or (runs >= 25 and strike_rate > 160): p.apply_game_performance_on_form(1)
                elif runs == 0: p.apply_game_performance_on_form(-1)
        for p in lineup_bowl:
            data = bowler_stats.get(p.name, {}) if bowler_stats else {}
            balls = data.get("balls", p.stats["balls_bowled"])
            runs = data.get("runs", p.stats["runs_conceded"])
            wickets = data.get("wickets", p.stats["wickets"])
            if balls > 0:
                if wickets >= 3: p.apply_game_performance_on_form(1)
                elif runs >= 45 and wickets == 0: p.apply_game_performance_on_form(-1)
