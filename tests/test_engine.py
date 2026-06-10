"""Tests for `engine.MatchEngine`: per-ball outcome sampling and post-match form evaluation.

`simulate_ball` is stochastic, so these tests check statistical properties
over many samples (valid outcome set, monotonic skill effects, aggression/
intent biases) rather than exact outcomes. `eval_match_performances_for_form`
is deterministic given fixed stat inputs and is checked directly.
"""
import random
from collections import Counter

import pytest

from cricket_sim_engine.engine import MatchEngine
from cricket_sim_engine.models import Player

pytestmark = pytest.mark.unit


def make_player(name="P", role="Batsman", batting_ovr=70, bowling_ovr=20, **kwargs):
    defaults = dict(
        is_overseas=False, age=27, batting_hand="Right", bowling_hand="Right",
        batting_archetype="Strike Rotator", bowling_phase="Flexible", bowling_type="None",
        strengths="", weaknesses="",
    )
    defaults.update(kwargs)
    p = Player(name, role, max(batting_ovr, bowling_ovr), batting_ovr, bowling_ovr,
               defaults["is_overseas"], defaults["age"], defaults["batting_hand"], defaults["bowling_hand"],
               defaults["batting_archetype"], defaults["bowling_phase"], defaults["bowling_type"],
               defaults["strengths"], defaults["weaknesses"])
    p.match_phase = "Middle Overs"
    p.batting_aggression = 3
    p.bowling_aggression = 2
    return p


VALID_OUTCOMES = {"W", "0", "1", "2", "3", "4", "6"}


def sample_outcomes(engine, batter, bowler, n=2000, seed=1):
    random.seed(seed)
    return Counter(engine.simulate_ball(batter, bowler) for _ in range(n))


# --- basic outcome validity ----------------------------------------------------

def test_simulate_ball_returns_valid_outcome():
    engine = MatchEngine(difficulty="hard")
    batter = make_player(name="Bat", batting_ovr=70)
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=70, bowling_type="Right-arm Fast")
    for _ in range(200):
        outcome = engine.simulate_ball(batter, bowler)
        assert outcome in VALID_OUTCOMES


def test_simulate_ball_distribution_sums_to_all_outcomes():
    engine = MatchEngine(difficulty="hard")
    batter = make_player(batting_ovr=70)
    bowler = make_player(role="Bowler (Fast)", bowling_ovr=50, bowling_type="Right-arm Fast")
    counts = sample_outcomes(engine, batter, bowler, n=3000)
    assert set(counts) <= VALID_OUTCOMES
    assert sum(counts.values()) == 3000


# --- skill delta effects ---------------------------------------------------------

def test_better_batter_takes_fewer_wickets_and_more_boundaries():
    engine = MatchEngine(difficulty="hard")
    strong_batter = make_player(name="Strong", batting_ovr=95)
    weak_batter = make_player(name="Weak", batting_ovr=20)
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=70, bowling_type="Right-arm Fast")

    strong_counts = sample_outcomes(engine, strong_batter, bowler, n=4000, seed=10)
    weak_counts = sample_outcomes(engine, weak_batter, bowler, n=4000, seed=10)

    strong_wicket_rate = strong_counts["W"] / 4000
    weak_wicket_rate = weak_counts["W"] / 4000
    assert strong_wicket_rate < weak_wicket_rate

    strong_boundary_rate = (strong_counts["4"] + strong_counts["6"]) / 4000
    weak_boundary_rate = (weak_counts["4"] + weak_counts["6"]) / 4000
    assert strong_boundary_rate > weak_boundary_rate


def test_better_bowler_takes_more_wickets():
    engine = MatchEngine(difficulty="hard")
    batter = make_player(name="Bat", batting_ovr=60)
    strong_bowler = make_player(name="StrongBowl", role="Bowler (Fast)", bowling_ovr=90, bowling_type="Right-arm Fast")
    weak_bowler = make_player(name="WeakBowl", role="Bowler (Fast)", bowling_ovr=20, bowling_type="Right-arm Fast")

    strong_counts = sample_outcomes(engine, batter, strong_bowler, n=4000, seed=20)
    weak_counts = sample_outcomes(engine, batter, weak_bowler, n=4000, seed=20)

    assert strong_counts["W"] > weak_counts["W"]


# --- difficulty edge ---------------------------------------------------------------

@pytest.mark.parametrize("difficulty, expected_edge", [("easy", 0.18), ("medium", 0.09), ("hard", 0.0)])
def test_difficulty_edge_helps_user_team_batter(difficulty, expected_edge):
    engine = MatchEngine(user_team_name="User Team", difficulty=difficulty)
    user_batter = make_player(name="UserBat", batting_ovr=50)
    user_batter.team_name = "User Team"
    cpu_bowler = make_player(name="CPUBowl", role="Bowler (Fast)", bowling_ovr=50, bowling_type="Right-arm Fast")
    cpu_bowler.team_name = "CPU Team"

    cpu_batter = make_player(name="CPUBat", batting_ovr=50)
    cpu_batter.team_name = "CPU Team"

    user_counts = sample_outcomes(engine, user_batter, cpu_bowler, n=4000, seed=30)
    cpu_counts = sample_outcomes(engine, cpu_batter, cpu_bowler, n=4000, seed=30)

    user_wicket_rate = user_counts["W"] / 4000
    cpu_wicket_rate = cpu_counts["W"] / 4000
    if expected_edge > 0:
        assert user_wicket_rate < cpu_wicket_rate
    else:
        # Hard mode: no edge, distributions should be (statistically) identical
        # since both batters/bowlers have identical ratings and the same seed.
        assert user_counts == cpu_counts


def test_unknown_difficulty_falls_back_to_no_edge():
    engine = MatchEngine(user_team_name="User Team", difficulty="impossible")
    batter = make_player(batting_ovr=50)
    batter.team_name = "User Team"
    bowler = make_player(role="Bowler (Fast)", bowling_ovr=50, bowling_type="Right-arm Fast")
    bowler.team_name = "CPU"
    # Should not raise, and should behave like "hard" (no edge applied).
    outcome = engine.simulate_ball(batter, bowler)
    assert outcome in VALID_OUTCOMES


# --- archetype / phase synergy --------------------------------------------------

def test_finisher_in_death_overs_hits_more_boundaries_than_in_middle_overs():
    engine = MatchEngine(difficulty="hard")
    finisher_death = make_player(name="Finisher", batting_ovr=70, batting_archetype="Finisher")
    finisher_death.match_phase = "Death Overs"
    finisher_middle = make_player(name="Finisher", batting_ovr=70, batting_archetype="Finisher")
    finisher_middle.match_phase = "Middle Overs"
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")

    death_counts = sample_outcomes(engine, finisher_death, bowler, n=4000, seed=40)
    middle_counts = sample_outcomes(engine, finisher_middle, bowler, n=4000, seed=40)

    death_boundary_rate = (death_counts["4"] + death_counts["6"]) / 4000
    middle_boundary_rate = (middle_counts["4"] + middle_counts["6"]) / 4000
    assert death_boundary_rate > middle_boundary_rate


# --- batting/bowling aggression --------------------------------------------------

def test_higher_batting_aggression_increases_wickets_and_boundaries():
    engine = MatchEngine(difficulty="hard")
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")

    cautious = make_player(name="Cautious", batting_ovr=70)
    cautious.batting_aggression = 1
    aggressive = make_player(name="Aggressive", batting_ovr=70)
    aggressive.batting_aggression = 5

    cautious_counts = sample_outcomes(engine, cautious, bowler, n=4000, seed=50)
    aggressive_counts = sample_outcomes(engine, aggressive, bowler, n=4000, seed=50)

    assert aggressive_counts["W"] > cautious_counts["W"]
    aggressive_boundary = aggressive_counts["4"] + aggressive_counts["6"]
    cautious_boundary = cautious_counts["4"] + cautious_counts["6"]
    assert aggressive_boundary > cautious_boundary


def test_higher_bowling_aggression_increases_wickets():
    engine = MatchEngine(difficulty="hard")
    batter = make_player(name="Bat", batting_ovr=70)

    defensive_bowler = make_player(name="Def", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")
    defensive_bowler.bowling_aggression = 1
    attacking_bowler = make_player(name="Att", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")
    attacking_bowler.bowling_aggression = 5

    defensive_counts = sample_outcomes(engine, batter, defensive_bowler, n=4000, seed=60)
    attacking_counts = sample_outcomes(engine, batter, attacking_bowler, n=4000, seed=60)

    assert attacking_counts["W"] > defensive_counts["W"]


# --- batter intent ------------------------------------------------------------------

def test_aggressive_intent_increases_wickets_and_sixes():
    engine = MatchEngine(difficulty="hard")
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")

    normal = make_player(name="Normal", batting_ovr=70)
    normal.intent = "Normal"
    aggressive = make_player(name="Aggressive", batting_ovr=70)
    aggressive.intent = "Aggressive"

    normal_counts = sample_outcomes(engine, normal, bowler, n=4000, seed=70)
    aggressive_counts = sample_outcomes(engine, aggressive, bowler, n=4000, seed=70)

    assert aggressive_counts["W"] > normal_counts["W"]
    assert aggressive_counts["6"] > normal_counts["6"]


def test_defensive_intent_decreases_wickets_and_sixes():
    engine = MatchEngine(difficulty="hard")
    bowler = make_player(name="Bowl", role="Bowler (Fast)", bowling_ovr=60, bowling_type="Right-arm Fast")

    normal = make_player(name="Normal", batting_ovr=70)
    normal.intent = "Normal"
    defensive = make_player(name="Defensive", batting_ovr=70)
    defensive.intent = "Defensive"

    normal_counts = sample_outcomes(engine, normal, bowler, n=4000, seed=80)
    defensive_counts = sample_outcomes(engine, defensive, bowler, n=4000, seed=80)

    assert defensive_counts["W"] < normal_counts["W"]
    assert defensive_counts["6"] < normal_counts["6"]


# --- left/right-handed matchups -----------------------------------------------------

def test_left_handed_batter_vs_right_arm_spin_gets_boost():
    engine = MatchEngine(difficulty="hard")
    spinner_right = make_player(name="Spin", role="Bowler (Spin)", bowling_ovr=60, bowling_hand="Right", bowling_type="Off Spin")

    left_batter = make_player(name="LeftBat", batting_ovr=70, batting_hand="Left")
    right_batter = make_player(name="RightBat", batting_ovr=70, batting_hand="Right")

    left_counts = sample_outcomes(engine, left_batter, spinner_right, n=4000, seed=90)
    right_counts = sample_outcomes(engine, right_batter, spinner_right, n=4000, seed=90)

    # Left-handers vs right-arm spin get a positive skill_delta multiplier,
    # which should translate to fewer wickets for the same underlying ratings.
    assert left_counts["W"] <= right_counts["W"]


# --- eval_match_performances_for_form -------------------------------------------------

def test_half_century_boosts_batter_form():
    engine = MatchEngine()
    p = make_player(name="Batter", age=27)
    p.form = 5
    stats = {"Batter": {"runs": 60, "balls": 40}}
    engine.eval_match_performances_for_form([p], [], batter_stats=stats, bowler_stats={})
    assert p.form > 5


def test_fast_25_boosts_batter_form():
    engine = MatchEngine()
    p = make_player(name="Batter", age=27)
    p.form = 5
    stats = {"Batter": {"runs": 30, "balls": 15}}  # SR 200 > 160
    engine.eval_match_performances_for_form([p], [], batter_stats=stats, bowler_stats={})
    assert p.form > 5


def test_duck_lowers_batter_form():
    engine = MatchEngine()
    p = make_player(name="Batter", age=27)
    p.form = 5
    stats = {"Batter": {"runs": 0, "balls": 4}}
    engine.eval_match_performances_for_form([p], [], batter_stats=stats, bowler_stats={})
    assert p.form < 5


def test_did_not_bat_does_not_change_form():
    engine = MatchEngine()
    p = make_player(name="Batter", age=27)
    p.form = 5
    stats = {"Batter": {"runs": 0, "balls": 0}}
    engine.eval_match_performances_for_form([p], [], batter_stats=stats, bowler_stats={})
    assert p.form == 5


def test_three_wicket_haul_boosts_bowler_form():
    engine = MatchEngine()
    p = make_player(name="Bowler", role="Bowler (Fast)", age=27, bowling_ovr=70)
    p.form = 5
    stats = {"Bowler": {"runs": 30, "balls": 24, "wickets": 3}}
    engine.eval_match_performances_for_form([], [p], batter_stats={}, bowler_stats=stats)
    assert p.form > 5


def test_expensive_wicketless_spell_lowers_bowler_form():
    engine = MatchEngine()
    p = make_player(name="Bowler", role="Bowler (Fast)", age=27, bowling_ovr=70)
    p.form = 5
    stats = {"Bowler": {"runs": 50, "balls": 24, "wickets": 0}}
    engine.eval_match_performances_for_form([], [p], batter_stats={}, bowler_stats=stats)
    assert p.form < 5


def test_did_not_bowl_does_not_change_form():
    engine = MatchEngine()
    p = make_player(name="Bowler", role="Bowler (Fast)", age=27, bowling_ovr=70)
    p.form = 5
    stats = {"Bowler": {"runs": 0, "balls": 0, "wickets": 0}}
    engine.eval_match_performances_for_form([], [p], batter_stats={}, bowler_stats=stats)
    assert p.form == 5


def test_eval_match_performances_falls_back_to_player_stats_when_no_match_stats_given():
    engine = MatchEngine()
    p = make_player(name="Batter", age=27)
    p.form = 5
    p.stats["runs"] = 75
    p.stats["balls_faced"] = 50
    engine.eval_match_performances_for_form([p], [], batter_stats=None, bowler_stats=None)
    assert p.form > 5
