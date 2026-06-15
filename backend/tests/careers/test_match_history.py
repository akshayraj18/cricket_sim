import uuid

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.career import Match as MatchRow, MatchBall as MatchBallRow, Player as PlayerRow

USER_TEAM = "Mumbai Mavericks"


async def _create_season_career(client: AsyncClient, headers: dict) -> dict:
    body = {
        "name": "Match History Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "rosters2026",
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_simulate_round_writes_match_history(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = uuid.UUID(career["id"])

    resp = await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(select(MatchRow).where(MatchRow.career_id == career_id))
    matches = result.scalars().all()
    assert len(matches) == 5

    for match in matches:
        assert match.stage == "league"
        assert match.round_num == 1
        assert match.season_year == 2026
        assert match.winner_name in (match.team1_name, match.team2_name)
        assert match.toss_winner in (match.team1_name, match.team2_name)
        assert match.toss_decision in ("bat", "bowl")
        assert match.team1_score["team"] == match.team1_name
        assert match.team2_score["team"] == match.team2_name
        assert "over_log" in match.team1_score

    # Man of the match resolves to a real, currently-rostered player.
    motm_ids = [m.motm_player_id for m in matches if m.motm_player_id]
    assert len(motm_ids) == 5
    result = await db_session.execute(select(PlayerRow).where(PlayerRow.id.in_(motm_ids)))
    assert {p.id for p in result.scalars().all()} == set(motm_ids)

    result = await db_session.execute(
        select(func.count()).select_from(MatchBallRow).where(MatchBallRow.match_id.in_([m.id for m in matches]))
    )
    assert result.scalar_one() > 0


async def test_simulate_round_does_not_duplicate_match_history(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = uuid.UUID(career["id"])

    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)

    result = await db_session.execute(select(func.count()).select_from(MatchRow).where(MatchRow.career_id == career_id))
    assert result.scalar_one() == 10


async def test_motm_player_id_stable_across_resyncs(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    """A match's `motm_player_id` should still resolve after later rounds re-sync the players table."""
    career = await _create_season_career(client, auth_headers)
    career_id = uuid.UUID(career["id"])

    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    result = await db_session.execute(select(MatchRow).where(MatchRow.career_id == career_id))
    round1_motm_ids = {m.id: m.motm_player_id for m in result.scalars().all()}

    # A second round re-runs `_sync_teams_and_players`, deleting/recreating player rows.
    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)

    result = await db_session.execute(select(PlayerRow.id).where(PlayerRow.career_id == career_id))
    current_player_ids = {row[0] for row in result.all()}

    for motm_id in round1_motm_ids.values():
        assert motm_id in current_player_ids


async def test_list_matches(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)

    resp = await client.get(f"/careers/{career_id}/matches", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    matches = resp.json()
    assert len(matches) == 5
    for match in matches:
        assert match["stage"] == "league"
        assert match["round_num"] == 1
        assert match["season_year"] == 2026
        assert "team1_score" not in match  # summary view omits scorecards


async def test_list_matches_filters_by_season(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)

    resp = await client.get(f"/careers/{career_id}/matches", params={"season_year": 2099}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []

    resp = await client.get(f"/careers/{career_id}/matches", params={"season_year": 2026}, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert len(resp.json()) == 5


async def test_get_match_detail_and_balls(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    await client.post(f"/careers/{career_id}/season/simulate-round", headers=auth_headers)
    matches = (await client.get(f"/careers/{career_id}/matches", headers=auth_headers)).json()
    match_id = matches[0]["id"]

    resp = await client.get(f"/careers/{career_id}/matches/{match_id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    assert detail["id"] == match_id
    assert detail["team1_score"]["team"] == detail["team1_name"]
    assert detail["team2_score"]["team"] == detail["team2_name"]
    assert detail["motm_player_name"]

    resp = await client.get(f"/careers/{career_id}/matches/{match_id}/balls", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    balls_payload = resp.json()
    assert balls_payload["match_id"] == match_id
    assert len(balls_payload["balls"]) > 0
    first_ball = balls_payload["balls"][0]
    assert first_ball["innings"] == 1
    assert first_ball["over_num"] == 1
    assert first_ball["ball_num"] == 1
    assert first_ball["bowler_name"]


async def test_get_match_not_found(client: AsyncClient, auth_headers: dict):
    career = await _create_season_career(client, auth_headers)
    career_id = career["id"]

    resp = await client.get(f"/careers/{career_id}/matches/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_matches_require_ownership(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/careers/{uuid.uuid4()}/matches", headers=auth_headers)
    assert resp.status_code == 404
