"""Coverage for `LeagueState` features not exercised by the draft/lineup/match-flow/
season-lifecycle suites: leaderboards, payload serialisation, MVP scoring,
player lookup, the all-time/2026-roster pool options, and save migration.
"""
import os

import pytest

from cricket_sim_engine.sim.league_state import LeagueState

pytestmark = pytest.mark.integration


# --- alternate league setup paths --------------------------------------------------

def test_new_league_alltime_pool_loads_legends():
    league = LeagueState()
    league.new_league("Mumbai Mavericks", "medium", "alltime")
    assert league.draft_pool_type == "alltime"
    names = {p.name for p in league.player_pool}
    assert "AB de Vylliers" in names


def test_new_league_unknown_draft_pool_falls_back_to_current():
    league = LeagueState()
    league.new_league("Mumbai Mavericks", "medium", "not-a-real-pool")
    assert league.draft_pool_type == "current"


def test_new_league_unknown_difficulty_falls_back_to_hard():
    league = LeagueState()
    league.new_league("Mumbai Mavericks", "not-a-real-difficulty")
    assert league.difficulty == "hard"


def test_new_league_with_rosters_assigns_real_2026_squads_to_all_teams():
    league = LeagueState()
    league.new_league_with_rosters("Chennai Cholas", "medium")
    assert league.phase == "season"
    for team in league.teams:
        assert len(team.roster) >= 18
        for p in team.roster:
            assert p.team_name == team.name


# --- payload serialisation ----------------------------------------------------------

def test_payload_structure_in_draft_phase(league):
    payload = league.payload()
    assert payload["phase"] == "draft"
    assert len(payload["teams"]) == 10
    assert payload["draft"]["available"]
    assert payload["draft"]["user_pick_position"] >= 1
    assert payload["live_match"] is None
    assert payload["save_exists"] in (True, False)


def test_payload_structure_in_season_phase(drafted):
    payload = drafted.payload()
    assert payload["phase"] == "season"
    assert len(payload["standings"]) == 10
    assert "tables" in payload and "leaderboards" in payload
    assert payload["tables"]["batting"] == []  # no balls bowled/faced yet
    assert payload["leaderboards"]["strike_rate"] == []  # qualification minimum not met


def test_team_dict_includes_branding_and_roster(drafted):
    team = drafted.user_team()
    team_dict = drafted.team_dict(team)
    assert team_dict["name"] == team.name
    assert "abbr" in team_dict and "primary" in team_dict
    assert len(team_dict["roster"]) == 21
    # roster sorted best-rated first
    ovrs = [p["ovr"] for p in team_dict["roster"]]
    assert ovrs == sorted(ovrs, reverse=True)


def test_player_dict_includes_derived_fields(drafted):
    team = drafted.user_team()
    p = team.roster[0]
    pdict = drafted.player_dict(p)
    assert pdict["name"] == p.name
    assert "ovr_progression" in pdict
    assert "phase_fit_powerplay" in pdict
    assert pdict["best_bowling"] == "-"  # no wickets taken yet
    assert pdict["mvp"] >= 0


# --- find_player_anywhere ------------------------------------------------------------

def test_find_player_anywhere_locates_rostered_player(drafted):
    team = drafted.user_team()
    target = team.roster[0]
    found = drafted.find_player_anywhere(target.name)
    assert found is target


def test_find_player_anywhere_locates_pool_player(drafted):
    if not drafted.player_pool:
        pytest.skip("no players left in the free-agent pool after a full draft")
    target = drafted.player_pool[0]
    found = drafted.find_player_anywhere(target.name)
    assert found is target


def test_find_player_anywhere_returns_none_for_unknown_name(drafted):
    assert drafted.find_player_anywhere("Nobody Real") is None


# --- mvp_score / leaderboards ---------------------------------------------------------

def test_mvp_score_rewards_runs_wickets_and_fielding(drafted):
    team = drafted.user_team()
    p = team.roster[0]
    baseline = drafted.mvp_score(p)
    p.stats["runs"] = 60
    p.stats["fours"] = 4
    p.stats["sixes"] = 2
    p.stats["fifties"] = 1
    after_batting = drafted.mvp_score(p)
    assert after_batting > baseline

    p.stats["wickets"] = 3
    p.stats["balls_bowled"] = 24
    p.stats["runs_conceded"] = 10
    after_bowling = drafted.mvp_score(p)
    assert after_bowling > after_batting

    p.stats["catches"] = 2
    p.stats["stumpings"] = 1
    p.stats["runouts"] = 1
    after_fielding = drafted.mvp_score(p)
    assert after_fielding > after_bowling

    p.stats["motm"] = 1
    after_motm = drafted.mvp_score(p)
    assert after_motm > after_fielding


def test_mvp_score_handles_missing_stat_fields_gracefully(drafted):
    team = drafted.user_team()
    p = team.roster[0]
    # Simulate an old save missing the lazily-added fields.
    for key in ("games", "team_wins"):
        p.stats.pop(key, None)
    score = drafted.mvp_score(p)
    assert score >= 0


def test_leaderboards_rate_categories_empty_before_any_matches(drafted):
    boards = drafted.leaderboards()
    # strike_rate/economy require a minimum balls faced/bowled, so nobody qualifies yet.
    assert boards["strike_rate"] == []
    assert boards["economy"] == []


def test_leaderboards_count_categories_list_all_players_with_zero_stats(drafted):
    boards = drafted.leaderboards()
    # No minimum threshold, so every rostered player qualifies (capped at 50).
    assert len(boards["orange_cap"]) == min(50, len(drafted.all_players()))
    assert all(p["runs"] == 0 for p in boards["orange_cap"])
    assert all(p["wickets"] == 0 for p in boards["purple_cap"])


def test_batting_and_bowling_tables_empty_before_any_matches(drafted):
    assert drafted.batting_table() == []
    assert drafted.bowling_table() == []


def test_leaderboard_respects_limit_and_minimum(drafted):
    team = drafted.user_team()
    for i, p in enumerate(team.roster):
        p.stats["runs"] = 100 - i
        p.stats["balls_faced"] = 30
    top = drafted.leaderboard(lambda p: p.stats["runs"], True, ("balls_faced", 1), 5)
    assert len(top) == 5
    assert top[0]["runs"] >= top[1]["runs"]


# --- best_bowling_label ----------------------------------------------------------------

def test_best_bowling_label_no_wickets_is_dash(drafted):
    team = drafted.user_team()
    p = team.roster[0]
    assert drafted.best_bowling_label(p) == "-"


def test_best_bowling_label_formats_wickets_and_runs(drafted):
    team = drafted.user_team()
    p = team.roster[0]
    p.stats["best_bowling_wickets"] = 4
    p.stats["best_bowling_runs"] = 22
    assert drafted.best_bowling_label(p) == "4/22"


# --- standings ordering -----------------------------------------------------------------

def test_standings_orders_by_points_then_nrr_then_wins(drafted):
    teams = drafted.teams
    teams[0].points, teams[0].wins, teams[0].runs_scored, teams[0].balls_faced, teams[0].runs_conceded, teams[0].balls_bowled = 10, 5, 200, 120, 150, 120
    teams[1].points, teams[1].wins, teams[1].runs_scored, teams[1].balls_faced, teams[1].runs_conceded, teams[1].balls_bowled = 10, 5, 220, 120, 150, 120
    table = drafted.standings()
    assert table[0] == teams[1]  # higher NRR wins the tiebreak
    assert table[1] == teams[0]


# --- save/load edge cases --------------------------------------------------------------

def test_save_slug_strips_unsafe_characters():
    assert LeagueState.save_slug("My Cool Career!!") == "my-cool-career"
    assert LeagueState.save_slug("  Spaces   Everywhere  ") == "spaces-everywhere"


def test_save_with_blank_name_raises_if_no_fallback():
    league = LeagueState()
    league.user_team_name = ""
    league.save_name = ""
    with pytest.raises(ValueError):
        league.save("   ")


def test_save_uses_user_team_as_fallback_name(drafted, tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(saves_dir))
    drafted.save_name = ""
    drafted.save()
    assert drafted.save_name == drafted.user_team_name
    assert os.path.exists(saves_dir / f"{LeagueState.save_slug(drafted.user_team_name)}.pkl")


def test_load_with_unknown_name_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVE_FILE", str(tmp_path / "missing.pkl"))
    with pytest.raises(ValueError):
        LeagueState.load("Nonexistent Save")


def test_delete_save_with_unknown_name_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    with pytest.raises(ValueError):
        LeagueState.delete_save("Nonexistent Save")


def test_list_saves_empty_when_no_saves_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "does-not-exist"))
    assert LeagueState.list_saves() == []


# --- migrate ----------------------------------------------------------------------------

def test_migrate_backfills_missing_attributes_on_old_state(drafted):
    league = drafted
    # Simulate an old pickled save missing newer attributes.
    del league.fixture_results
    del league.retention_limit
    del league.draft_pool_type
    del league.last_standings
    league.migrate()
    assert league.fixture_results == []
    assert league.retention_limit == 11
    assert league.draft_pool_type == "current"
    assert league.last_standings == []


def test_migrate_resets_invalid_difficulty(drafted):
    league = drafted
    league.difficulty = "extreme"
    league.migrate()
    assert league.difficulty == "hard"


def test_migrate_ensures_stat_fields_on_all_players(drafted):
    league = drafted
    team = league.user_team()
    for p in team.roster:
        p.stats.pop("games", None)
        p.stats.pop("team_wins", None)
    league.migrate()
    for p in team.roster:
        assert "games" in p.stats
        assert "team_wins" in p.stats


# --- find_team / user_team -----------------------------------------------------------

def test_find_team_unknown_name_raises(drafted):
    with pytest.raises(StopIteration):
        drafted.find_team("Not A Real Team")


def test_user_team_resolves_correct_franchise(drafted):
    assert drafted.user_team().name == drafted.user_team_name


# --- roster_needs / draft_score ------------------------------------------------------

def test_roster_needs_all_zero_for_full_balanced_squad(drafted):
    team = drafted.user_team()
    needs = drafted.roster_needs(team)
    # A fully-drafted 21-player squad should have no outstanding minimums.
    assert all(v == 0 for v in needs.values())


def test_roster_needs_nonzero_for_empty_squad(league):
    team = league.user_team()
    needs = league.roster_needs(team)
    assert needs["wk"] == 2
    assert needs["bat"] == 9
    assert needs["bowl"] == 9
