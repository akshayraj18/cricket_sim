"""Domain model unit tests: `Player` ratings/form/progression and `Team` records.

These exercise `models.py` directly (no league/match scaffolding needed),
covering the rating math (`current_*`, form impact), the position-derivation
table, post-match form swings, offseason progression, and `Team`'s
NRR/leadership helpers.
"""
import random

import pytest

from cricket_sim_engine.models import Player, Team, derive_preferred_position, ARCHETYPE_BATTING_POSITION, DEFAULT_BATTING_POSITION_BY_ROLE

pytestmark = pytest.mark.unit


def make_player(**overrides):
    defaults = dict(
        name="Test Player", role="Batsman", base_ovr=70, batting_ovr=70, bowling_ovr=20,
        is_overseas=False, age=27, batting_hand="Right", bowling_hand="Right",
        batting_archetype="Strike Rotator", bowling_phase="Flexible", bowling_type="None",
        strengths="", weaknesses="",
    )
    defaults.update(overrides)
    return Player(**defaults)


# --- derive_preferred_position -----------------------------------------------

def test_derive_preferred_position_uses_archetype_table():
    for (role, archetype), mean_pos in ARCHETYPE_BATTING_POSITION.items():
        pos = derive_preferred_position(role, archetype)
        assert pos == max(1, min(11, round(mean_pos)))


def test_derive_preferred_position_falls_back_to_role_default():
    pos = derive_preferred_position("Batsman", "Totally Unknown Archetype")
    assert pos == round(DEFAULT_BATTING_POSITION_BY_ROLE["Batsman"])


def test_derive_preferred_position_unknown_role_falls_back_to_six():
    pos = derive_preferred_position("Mystery Role", "Totally Unknown Archetype")
    assert pos == 6


def test_derive_preferred_position_clamped_to_1_through_11():
    pos_low = derive_preferred_position("Batsman", "Aggressive Opener")
    pos_high = derive_preferred_position("Bowler (Fast)", "Defensive Tailender")
    assert 1 <= pos_low <= 11
    assert 1 <= pos_high <= 11


def test_allrounder_batting_heavy_nudges_toward_top_order():
    bowling_heavy = derive_preferred_position("All-Rounder", "Anchor", batting_ovr=60, bowling_ovr=80)
    batting_heavy = derive_preferred_position("All-Rounder", "Anchor", batting_ovr=80, bowling_ovr=60)
    assert batting_heavy < bowling_heavy


def test_allrounder_small_gap_does_not_shift_position():
    baseline = derive_preferred_position("All-Rounder", "Anchor", batting_ovr=70, bowling_ovr=70)
    small_gap = derive_preferred_position("All-Rounder", "Anchor", batting_ovr=75, bowling_ovr=70)
    assert baseline == small_gap


# --- Player construction -------------------------------------------------------

def test_player_init_sets_preferred_position_and_defaults():
    p = make_player(role="Wicketkeeper", batting_archetype="Aggressive Opener", batting_ovr=85, bowling_ovr=20)
    assert p.preferred_position in (1, 2)
    assert p.form == 5
    assert p.intent == "Normal"
    assert p.team_name == "Unassigned"


def test_reset_stats_zeroes_all_fields():
    p = make_player()
    p.stats["runs"] = 50
    p.stats["wickets"] = 3
    p.reset_stats()
    assert p.stats["runs"] == 0
    assert p.stats["wickets"] == 0
    assert p.stats["best_bowling_runs"] == 999


# --- form / current ratings -----------------------------------------------------

@pytest.mark.parametrize("form, expected_impact", [(1, -4), (5, 0), (10, 5)])
def test_form_impact_range(form, expected_impact):
    p = make_player(batting_ovr=70, bowling_ovr=50)
    p.form = form
    assert p.form_impact == expected_impact


def test_current_batting_bowling_ovr_shift_with_form():
    p = make_player(base_ovr=70, batting_ovr=70, bowling_ovr=50)
    p.form = 10  # +5 impact
    assert p.current_batting == 75
    assert p.current_bowling == 55
    assert p.current_ovr == 75  # max(base, bat, bowl) + impact = 70 + 5


def test_current_ratings_clamped_to_1_and_100():
    p = make_player(base_ovr=99, batting_ovr=99, bowling_ovr=2)
    p.form = 10
    assert p.current_batting == 100  # clamped at 100, not 104
    p.form = 1
    assert p.current_bowling == 1  # clamped at 1, not -2


def test_current_ovr_uses_max_of_base_batting_bowling():
    p = make_player(base_ovr=50, batting_ovr=80, bowling_ovr=40)
    p.form = 5
    assert p.current_ovr == 80


# --- strike rate / economy -----------------------------------------------------

def test_batting_strike_rate_zero_when_no_balls_faced():
    p = make_player()
    assert p.batting_strike_rate == 0.0


def test_batting_strike_rate_computed_from_stats():
    p = make_player()
    p.stats["runs"] = 50
    p.stats["balls_faced"] = 25
    assert p.batting_strike_rate == 200.0


def test_bowling_economy_zero_when_no_balls_bowled():
    p = make_player()
    assert p.bowling_economy == 0.0


def test_bowling_economy_computed_from_stats():
    p = make_player()
    p.stats["runs_conceded"] = 24
    p.stats["balls_bowled"] = 12
    assert p.bowling_economy == 12.0  # 24 runs / 2 overs


# --- apply_game_performance_on_form ---------------------------------------------

@pytest.mark.parametrize("age, impact, expected_delta", [
    (22, 1, 1.35),   # young player, positive: +0.35 bonus
    (26, 1, 1.15),   # mid-career, positive: +0.15 bonus
    (36, 1, 0.65),   # veteran, positive: scaled by 0.65
    (30, 1, 1.0),    # prime-age, positive: unchanged
    (22, -1, -1.20), # young player, negative: amplified
    (36, -1, -0.70), # veteran, negative: dampened
    (30, -1, -1.0),  # prime-age, negative: unchanged
])
def test_apply_game_performance_on_form_age_bands(age, impact, expected_delta):
    p = make_player(age=age)
    p.form = 5
    p.apply_game_performance_on_form(impact)
    assert p.form == pytest.approx(5 + expected_delta)


def test_form_clamped_between_1_and_10():
    p = make_player(age=22)
    p.form = 9.9
    p.apply_game_performance_on_form(1)  # would push past 10
    assert p.form == 10

    p.form = 1.1
    p.apply_game_performance_on_form(-1)  # would push below 1
    assert p.form == 1


# --- apply_offseason_progression -------------------------------------------------

@pytest.mark.parametrize("age, possible_growth", [
    (20, [1, 2, 3, 4, 5]),
    (24, [0, 1, 2, 3, 4]),
    (28, [-1, 0, 1, 2]),
    (32, [-2, -1, 0, 1]),
    (37, [-5, -4, -3, -2, -1]),
])
def test_apply_offseason_progression_growth_within_age_band(age, possible_growth):
    random.seed(42)
    for _ in range(50):
        p = make_player(age=age, batting_ovr=50, bowling_ovr=50)
        before_bat = p.batting_ovr
        p.apply_offseason_progression()
        delta = p.batting_ovr - before_bat
        assert delta in possible_growth


def test_apply_offseason_progression_increments_age_resets_form_and_base_ovr():
    p = make_player(age=25, batting_ovr=70, bowling_ovr=40)
    p.form = 9
    p.apply_offseason_progression()
    assert p.age == 26
    assert p.form == 5
    assert p.base_ovr == max(p.batting_ovr, p.bowling_ovr)


def test_apply_offseason_progression_clamps_ratings_to_1_and_100():
    p = make_player(age=40, batting_ovr=2, bowling_ovr=1)
    for _ in range(20):
        p.apply_offseason_progression()
        assert 1 <= p.batting_ovr <= 100
        assert 1 <= p.bowling_ovr <= 100


# --- Team -------------------------------------------------------------------------

def test_team_init_defaults():
    team = Team("Test Team")
    assert team.roster == []
    assert team.points == 0
    assert team.games_played == 0
    assert team.captain is None
    assert team.saved_bat_to_bowl_sub == {"out": "", "in": ""}


def test_team_games_played_is_wins_plus_losses():
    team = Team("Test Team")
    team.wins = 7
    team.losses = 3
    assert team.games_played == 10


def test_net_run_rate_default_before_any_overs():
    team = Team("Test Team")
    assert team.net_run_rate == 0.0


def test_net_run_rate_computed_from_runs_and_balls():
    team = Team("Test Team")
    team.runs_scored = 180
    team.balls_faced = 120  # 20 overs
    team.runs_conceded = 150
    team.balls_bowled = 120  # 20 overs
    assert team.net_run_rate == pytest.approx(1.5)


def test_net_run_rate_can_be_negative():
    team = Team("Test Team")
    team.runs_scored = 120
    team.balls_faced = 120
    team.runs_conceded = 180
    team.balls_bowled = 120
    assert team.net_run_rate == pytest.approx(-3.0)


def test_auto_assign_cpu_leadership_picks_top_two_by_ovr():
    team = Team("Test Team")
    p1 = make_player(name="Best", base_ovr=90, batting_ovr=90, bowling_ovr=10)
    p2 = make_player(name="Second", base_ovr=85, batting_ovr=85, bowling_ovr=10)
    p3 = make_player(name="Third", base_ovr=60, batting_ovr=60, bowling_ovr=10)
    team.roster = [p3, p1, p2]
    team.auto_assign_cpu_leadership()
    assert team.captain == p1
    assert team.vice_captain == p2
