import uuid

from httpx import AsyncClient

from cricket_sim_engine.sim.league_state import LeagueState

USER_TEAM = "Mumbai Indians"


async def _create_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "My Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "current",
        **overrides,
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_create_career_returns_full_state(client: AsyncClient, auth_headers: dict):
    body = await _create_career(client, auth_headers)

    assert body["name"] == "My Career"
    assert body["user_team_name"] == USER_TEAM
    assert body["difficulty"] == "medium"
    assert body["draft_pool_type"] == "current"
    assert body["phase"] == "draft"
    assert body["season_year"] == 2026
    assert "state" in body
    assert body["state"]["phase"] == "draft"
    assert len(body["state"]["teams"]) == 10


async def test_create_career_requires_auth(client: AsyncClient):
    resp = await client.post("/careers", json={
        "name": "My Career", "user_team_name": USER_TEAM, "difficulty": "medium", "draft_pool_type": "current",
    })
    assert resp.status_code == 401


async def test_create_career_rejects_invalid_team(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/careers", json={
        "name": "Bad Career", "user_team_name": "Not A Real Team",
        "difficulty": "medium", "draft_pool_type": "current",
    }, headers=auth_headers)
    assert resp.status_code == 400


async def test_create_career_rejects_duplicate_name(client: AsyncClient, auth_headers: dict):
    await _create_career(client, auth_headers, name="Dup")
    resp = await client.post("/careers", json={
        "name": "Dup", "user_team_name": USER_TEAM, "difficulty": "medium", "draft_pool_type": "current",
    }, headers=auth_headers)
    assert resp.status_code == 400


async def test_list_careers(client: AsyncClient, auth_headers: dict):
    await _create_career(client, auth_headers, name="Career One")
    await _create_career(client, auth_headers, name="Career Two")

    resp = await client.get("/careers", headers=auth_headers)
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert names == {"Career One", "Career Two"}


async def test_list_careers_scoped_to_user(client: AsyncClient, auth_headers: dict):
    await _create_career(client, auth_headers, name="Mine")

    other_resp = await client.post("/auth/guest")
    other_headers = {"Authorization": f"Bearer {other_resp.json()['tokens']['access_token']}"}

    resp = await client.get("/careers", headers=other_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_career_detail(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    resp = await client.get(f"/careers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]
    assert resp.json()["state"]["user_team_name"] == USER_TEAM


async def test_get_career_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get(f"/careers/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_career_not_owned_by_user(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    other_resp = await client.post("/auth/guest")
    other_headers = {"Authorization": f"Bearer {other_resp.json()['tokens']['access_token']}"}

    resp = await client.get(f"/careers/{created['id']}", headers=other_headers)
    assert resp.status_code == 404


async def test_save_career_state_round_trip(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    league = LeagueState.from_dict(created["state"])
    league.start_draft()
    league.autodraft_to_end()
    assert league.phase == "season"

    resp = await client.put(f"/careers/{created['id']}/state", json=league.to_dict(), headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["phase"] == "season"
    assert body["state"]["phase"] == "season"
    assert all(len(t["roster"]) == 21 for t in body["state"]["teams"])

    # Reload from a fresh GET to confirm it persisted.
    resp = await client.get(f"/careers/{created['id']}", headers=auth_headers)
    assert resp.json()["phase"] == "season"


async def test_save_career_state_discards_live_match(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    league = LeagueState.from_dict(created["state"])
    league.start_draft()
    league.autodraft_to_end()
    league.begin_match_day(interactive=True)
    assert league.live_match is not None

    resp = await client.put(f"/careers/{created['id']}/state", json=league.to_dict(), headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert "live_match" not in resp.json()["state"] or resp.json()["state"].get("live_match") is None


async def test_save_career_state_invalid_body(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    resp = await client.put(f"/careers/{created['id']}/state", json={"not": "a valid state"}, headers=auth_headers)
    assert resp.status_code == 400


async def test_save_career_state_not_found(client: AsyncClient, auth_headers: dict):
    league = LeagueState()
    league.new_league(USER_TEAM, "medium")

    resp = await client.put(f"/careers/{uuid.uuid4()}/state", json=league.to_dict(), headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_career(client: AsyncClient, auth_headers: dict):
    created = await _create_career(client, auth_headers)

    resp = await client.delete(f"/careers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = await client.get(f"/careers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_career_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.delete(f"/careers/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_create_career_with_2026_rosters(client: AsyncClient, auth_headers: dict):
    body = await _create_career(client, auth_headers, name="2026 Career", draft_pool_type="rosters2026")

    assert body["phase"] == "season"
    assert body["draft_pool_type"] == "rosters2026"
    assert all(len(t["roster"]) >= 11 for t in body["state"]["teams"])
