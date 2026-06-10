"""Unit tests for the small role/phase classification helpers in `sim/helpers.py`.

These are pure, stateless functions used throughout lineup selection and
serialisation, so they're tested directly against constructed `Player`s
without any league/match scaffolding.
"""
import pytest

from models import Player
from sim.helpers import (
    allrounder_counts_as_bat,
    allrounder_counts_as_bowl,
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


def make_player(role="Batsman", batting_ovr=70, bowling_ovr=20, **kwargs):
    defaults = dict(
        name="P", base_ovr=max(batting_ovr, bowling_ovr), is_overseas=False, age=25,
        batting_archetype="Strike Rotator", bowling_phase="Flexible", bowling_type="None",
        strengths="", weaknesses="",
    )
    defaults.update(kwargs)
    return Player("P", role, defaults["base_ovr"], batting_ovr, bowling_ovr, defaults["is_overseas"], defaults["age"],
                   batting_archetype=defaults["batting_archetype"], bowling_phase=defaults["bowling_phase"],
                   bowling_type=defaults["bowling_type"], strengths=defaults["strengths"], weaknesses=defaults["weaknesses"])


# --- role classification --------------------------------------------------------

@pytest.mark.parametrize("role, expected", [
    ("Batsman", True), ("Wicketkeeper", True), ("All-Rounder", True),
    ("Bowler (Fast)", False), ("Bowler (Spin)", False),
])
def test_is_batting_role(role, expected):
    assert is_batting_role(make_player(role=role)) is expected


@pytest.mark.parametrize("role, expected", [
    ("Bowler (Fast)", True), ("Bowler (Spin)", True), ("All-Rounder", True),
    ("Batsman", False), ("Wicketkeeper", False),
])
def test_is_bowling_role(role, expected):
    assert is_bowling_role(make_player(role=role)) is expected


def test_allrounder_counts_as_bat_when_batting_ge_bowling():
    p = make_player(role="All-Rounder", batting_ovr=70, bowling_ovr=60)
    assert allrounder_counts_as_bat(p) is True
    assert allrounder_counts_as_bowl(p) is False


def test_allrounder_counts_as_bowl_when_bowling_ge_batting():
    p = make_player(role="All-Rounder", batting_ovr=60, bowling_ovr=70)
    assert allrounder_counts_as_bowl(p) is True
    assert allrounder_counts_as_bat(p) is False


def test_allrounder_counts_as_both_when_equal():
    p = make_player(role="All-Rounder", batting_ovr=65, bowling_ovr=65)
    assert allrounder_counts_as_bat(p) is True
    assert allrounder_counts_as_bowl(p) is True


def test_non_allrounder_never_counts_as_allrounder_bat_or_bowl():
    p = make_player(role="Batsman", batting_ovr=80, bowling_ovr=80)
    assert allrounder_counts_as_bat(p) is False
    assert allrounder_counts_as_bowl(p) is False


@pytest.mark.parametrize("role, batting_ovr, bowling_ovr, expected", [
    ("Batsman", 70, 20, True),
    ("Wicketkeeper", 70, 20, True),
    ("Bowler (Fast)", 20, 70, False),
    ("All-Rounder", 70, 60, True),  # batting >= bowling -> counts as bat slot
    ("All-Rounder", 60, 70, False),
])
def test_batting_slot_player(role, batting_ovr, bowling_ovr, expected):
    p = make_player(role=role, batting_ovr=batting_ovr, bowling_ovr=bowling_ovr)
    assert batting_slot_player(p) is expected


@pytest.mark.parametrize("role, batting_ovr, bowling_ovr, expected", [
    ("Bowler (Fast)", 20, 70, True),
    ("Bowler (Spin)", 20, 70, True),
    ("Batsman", 70, 20, False),
    ("All-Rounder", 60, 70, True),  # bowling >= batting -> counts as bowl slot
    ("All-Rounder", 70, 60, False),
])
def test_bowling_slot_player(role, batting_ovr, bowling_ovr, expected):
    p = make_player(role=role, batting_ovr=batting_ovr, bowling_ovr=bowling_ovr)
    assert bowling_slot_player(p) is expected


@pytest.mark.parametrize("role, expected", [
    ("Batsman", True), ("Wicketkeeper", True), ("All-Rounder", True),
    ("Bowler (Fast)", False), ("Bowler (Spin)", False),
])
def test_counts_as_batter(role, expected):
    assert counts_as_batter(make_player(role=role)) is expected


@pytest.mark.parametrize("role, expected", [
    ("Bowler (Fast)", True), ("Bowler (Spin)", True), ("All-Rounder", True),
    ("Batsman", False), ("Wicketkeeper", False),
])
def test_counts_as_bowler(role, expected):
    assert counts_as_bowler(make_player(role=role)) is expected


@pytest.mark.parametrize("role, expected", [
    ("Wicketkeeper", True), ("Batsman", False), ("All-Rounder", False), ("Bowler (Spin)", False),
])
def test_is_wicketkeeper_option(role, expected):
    assert is_wicketkeeper_option(make_player(role=role)) is expected


# --- ordinal ----------------------------------------------------------------------

@pytest.mark.parametrize("number, expected", [
    (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
    (11, "11th"), (12, "12th"), (13, "13th"),
    (21, "21st"), (22, "22nd"), (23, "23rd"),
    (100, "100th"), (101, "101st"), (111, "111th"), (112, "112th"),
])
def test_ordinal(number, expected):
    assert ordinal(number) == expected


# --- bowling_kind -------------------------------------------------------------------

@pytest.mark.parametrize("bowling_type, expected", [
    ("Right-arm Fast", "pace"),
    ("Left-arm Orthodox", "spin"),
    ("Leg Spin", "spin"),
    ("Off Spin", "spin"),
    ("Right-arm Medium", "pace"),
    ("None", "part-time"),
    ("", "part-time"),
])
def test_bowling_kind(bowling_type, expected):
    p = make_player(role="Bowler (Fast)", bowling_type=bowling_type)
    assert bowling_kind(p) == expected


# --- innings_phase ------------------------------------------------------------------

@pytest.mark.parametrize("over_num, expected", [
    (0, "Powerplay"), (5, "Powerplay"),
    (6, "Middle Overs"), (14, "Middle Overs"),
    (15, "Death Overs"), (19, "Death Overs"),
])
def test_innings_phase(over_num, expected):
    assert innings_phase(over_num) == expected


# --- ensure_stat_fields ---------------------------------------------------------------

def test_ensure_stat_fields_backfills_missing_keys():
    p = make_player()
    # These keys aren't part of the base `reset_stats` shape — they're
    # backfilled lazily by `ensure_stat_fields` (e.g. for older saves).
    assert "best_bowling_against" not in p.stats
    assert "games" not in p.stats
    ensure_stat_fields(p)
    assert p.stats["maidens"] == 0
    assert p.stats["best_bowling_runs"] == 999
    assert p.stats["games"] == 0
    assert p.stats["best_bowling_against"] == ""


def test_ensure_stat_fields_does_not_overwrite_existing_values():
    p = make_player()
    p.stats["motm"] = 3
    ensure_stat_fields(p)
    assert p.stats["motm"] == 3


# --- expanded_batting_archetype ----------------------------------------------------

def test_expanded_batting_archetype_aggressor_high_rated_is_aggressive_opener():
    p = make_player(batting_archetype="Aggressor", batting_ovr=80, bowling_ovr=10)
    assert expanded_batting_archetype(p) == "Aggressive Opener"


def test_expanded_batting_archetype_aggressor_low_rated_is_pace_specialist():
    p = make_player(batting_archetype="Aggressor", batting_ovr=50, bowling_ovr=10)
    assert expanded_batting_archetype(p) == "Pace Specialist"


def test_expanded_batting_archetype_strike_rotator_becomes_middle_over_rotator():
    p = make_player(batting_archetype="Strike Rotator")
    assert expanded_batting_archetype(p) == "Middle-over Rotator"


def test_expanded_batting_archetype_passes_through_other_labels():
    p = make_player(batting_archetype="Finisher")
    assert expanded_batting_archetype(p) == "Finisher"


# --- expanded_bowling_phase ----------------------------------------------------------

def test_expanded_bowling_phase_mystery_spin():
    p = make_player(role="Bowler (Spin)", bowling_type="Mystery Spin", bowling_phase="Middle Overs")
    assert expanded_bowling_phase(p) == "Mystery Spinner"


def test_expanded_bowling_phase_mystery_pace():
    p = make_player(role="Bowler (Fast)", bowling_type="Mystery Variations", bowling_phase="Death Overs")
    assert expanded_bowling_phase(p) == "Mystery Pace"


def test_expanded_bowling_phase_new_ball():
    p = make_player(role="Bowler (Fast)", bowling_type="Right-arm Fast", bowling_phase="New Ball")
    assert expanded_bowling_phase(p) == "New-ball Bowler"


def test_expanded_bowling_phase_death_overs():
    p = make_player(role="Bowler (Fast)", bowling_type="Right-arm Fast", bowling_phase="Death Overs")
    assert expanded_bowling_phase(p) == "Death-over Specialist"


def test_expanded_bowling_phase_middle_over_spinner():
    p = make_player(role="Bowler (Spin)", bowling_type="Left-arm Orthodox", bowling_phase="Middle Overs")
    assert expanded_bowling_phase(p) == "Middle-over Spinner"


def test_expanded_bowling_phase_part_time():
    p = make_player(role="All-Rounder", bowling_type="Right-arm Medium", bowling_phase="Part-time")
    assert expanded_bowling_phase(p) == "Part-time Option"


def test_expanded_bowling_phase_passes_through_flexible():
    p = make_player(role="All-Rounder", bowling_type="Right-arm Medium", bowling_phase="Flexible")
    assert expanded_bowling_phase(p) == "Flexible"


# --- phase_fit_label -----------------------------------------------------------------

def test_phase_fit_label_batting_strength_powerplay():
    p = make_player(batting_archetype="Aggressor")
    label = phase_fit_label(p, "Powerplay")
    assert "batting strength" in label


def test_phase_fit_label_bowling_phase_match():
    p = make_player(role="Bowler (Fast)", bowling_phase="Death Overs", bowling_type="Right-arm Fast")
    label = phase_fit_label(p, "Death Overs")
    assert "bowling phase" in label
    assert "death skill" in label


def test_phase_fit_label_new_ball_swing_powerplay():
    p = make_player(role="Bowler (Fast)", bowling_type="Left-arm Swing", bowling_phase="Flexible")
    label = phase_fit_label(p, "Powerplay")
    assert "new-ball movement" in label


def test_phase_fit_label_middle_over_spin():
    p = make_player(role="Bowler (Spin)", bowling_type="Leg Spin", bowling_phase="Flexible")
    label = phase_fit_label(p, "Middle Overs")
    assert "middle-over spin" in label


def test_phase_fit_label_empty_when_no_fit():
    p = make_player(role="Batsman", batting_archetype="Anchor", bowling_phase="Flexible", bowling_type="None")
    label = phase_fit_label(p, "Death Overs")
    assert label == ""
