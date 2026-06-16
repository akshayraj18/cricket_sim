"""Whole-career lifecycle: simulating a full league stage through playoffs, retention, and save/load round-tripping."""
import os

import pytest

from cricket_sim_engine.sim.league_state import LeagueState

pytestmark = pytest.mark.regression


def _simulate_to_league_complete(league):
    while league.phase == "season":
        league.simulate_current_round()
    return league


def test_simulating_all_14_rounds_reaches_league_complete(drafted):
    league = drafted
    league.set_leadership(league.user_team().captain.name, league.user_team().vice_captain.name)
    _simulate_to_league_complete(league)
    assert league.phase == "league_complete"
    assert league.round_num == 15
    assert len(league.pending_playoff_top_four) == 4
    for team in league.teams:
        assert team.games_played == 14, f"{team.name} played {team.games_played} games"


def test_schedule_meets_pairing_constraints(drafted):
    """The 14-round schedule must: play every round as a perfect matching of
    all 10 teams (so each team plays 14 games and appears once per round),
    have every pair of teams meet at least once, and never schedule any pair
    3+ times. Re-built many times since the schedule is randomised."""
    from collections import Counter

    league = drafted
    team_names = {t.name for t in league.teams}
    assert len(team_names) == 10

    for _ in range(50):
        schedule = league.build_schedule()
        assert len(schedule) == 14

        games = Counter()
        pair_counts = Counter()
        for round_ in schedule:
            # perfect matching: 5 disjoint pairs covering all 10 teams
            assert len(round_) == 5
            in_round = [name for pair in round_ for name in pair]
            assert sorted(in_round) == sorted(team_names), "round is not a perfect matching"
            for a, b in round_:
                games[a] += 1
                games[b] += 1
                pair_counts[frozenset((a, b))] += 1

        assert all(v == 14 for v in games.values()), f"a team did not play 14 games: {games}"

        all_pairs = {
            frozenset((a, b))
            for a in team_names
            for b in team_names
            if a < b
        }
        assert set(pair_counts) == all_pairs, "not every pair of teams meets"
        assert max(pair_counts.values()) <= 2, "a pair was scheduled 3+ times"
        # 9 single-RR rounds + 5 replayed rounds => exactly 25 second meetings.
        assert sum(1 for v in pair_counts.values() if v == 2) == 25


def test_standings_are_internally_consistent_after_a_season(drafted):
    league = drafted
    league.set_leadership(league.user_team().captain.name, league.user_team().vice_captain.name)
    _simulate_to_league_complete(league)
    table = league.standings()
    assert len(table) == 10
    assert sum(t.wins for t in table) == sum(t.losses for t in table)
    assert all(t.points == t.wins * 2 for t in table)


def test_playoffs_run_to_a_champion(drafted):
    league = drafted
    league.set_leadership(league.user_team().captain.name, league.user_team().vice_captain.name)
    _simulate_to_league_complete(league)
    league.start_playoffs()
    assert league.phase == "playoffs"
    assert len(league.playoff_matches) == 4

    guard = 0
    while league.phase == "playoffs":
        league.simulate_current_round()
        guard += 1
        assert guard <= 10, "playoffs did not converge"

    assert league.phase == "season_end"
    assert league.playoff_results[-1]["winner"] in [t.name for t in league.teams]


def test_retention_window_resets_squads_and_starts_new_draft(drafted):
    league = drafted
    user = league.user_team()
    league.set_leadership(user.captain.name, user.vice_captain.name)
    _simulate_to_league_complete(league)
    league.start_playoffs()
    guard = 0
    while league.phase == "playoffs":
        league.simulate_current_round()
        guard += 1
        assert guard <= 10

    assert league.phase == "season_end"
    league.open_retention()
    assert league.phase == "retention"
    limit = league.retention_limit

    keep_names = [p.name for p in user.roster[:limit]]
    league.submit_retentions(keep_names)

    assert league.phase == "draft"
    assert league.season_year == 2027
    assert set(p.name for p in user.roster) == set(keep_names)
    for team in league.teams:
        # CPU teams may have already picked once or twice via cpu_until_user()
        # before the user's first turn, so rosters can sit at >= the retention limit.
        assert len(team.roster) >= limit
        assert team.points == 0 and team.wins == 0 and team.losses == 0


def test_retention_rejects_wrong_player_count(drafted):
    league = drafted
    user = league.user_team()
    league.set_leadership(user.captain.name, user.vice_captain.name)
    _simulate_to_league_complete(league)
    league.start_playoffs()
    guard = 0
    while league.phase == "playoffs":
        league.simulate_current_round()
        guard += 1
        assert guard <= 10
    league.open_retention()
    with pytest.raises(ValueError):
        league.submit_retentions([p.name for p in user.roster[:3]])


def test_save_and_load_round_trips_state(drafted, tmp_path, monkeypatch):
    saves_dir = tmp_path / "saves"
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(saves_dir))
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVE_FILE", str(tmp_path / "missing.pkl"))

    league = drafted
    league.set_leadership(league.user_team().captain.name, league.user_team().vice_captain.name)
    league.save("My Career")
    assert os.path.exists(saves_dir / "my-career.pkl")

    saves = LeagueState.list_saves()
    assert any(s["name"] == "My Career" for s in saves)

    loaded = LeagueState.load("My Career")
    assert loaded.user_team_name == league.user_team_name
    assert loaded.phase == league.phase
    assert len(loaded.user_team().roster) == len(league.user_team().roster)
    assert loaded.user_team().captain.name == league.user_team().captain.name

    LeagueState.delete_save("My Career")
    assert not os.path.exists(saves_dir / "my-career.pkl")


def test_load_without_a_save_file_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVES_DIR", str(tmp_path / "saves"))
    monkeypatch.setattr("cricket_sim_engine.sim.league_state.SAVE_FILE", str(tmp_path / "missing.pkl"))
    with pytest.raises(ValueError):
        LeagueState.load()
