"""Player-name override endpoints, and their effect on career creation."""
import csv
import io

from httpx import AsyncClient

USER_TEAM = "Mumbai Mavericks"


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text, newline="")))


def _csv(pairs) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["player_key", "name"], lineterminator="\r\n")
    writer.writeheader()
    for key, name in pairs:
        writer.writerow({"player_key": key, "name": name})
    return buf.getvalue()


async def _create_career(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "name": "Names Career",
        "user_team_name": USER_TEAM,
        "difficulty": "medium",
        "draft_pool_type": "rosters2026",
        **overrides,
    }
    resp = await client.post("/careers", json=body, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _career_names(career: dict) -> set[str]:
    return {
        p["name"]
        for team in career["state"]["teams"]
        for p in team["roster"]
    }


async def test_export_lists_every_player_defaulting_to_the_shipped_name(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.get("/auth/me/player-names.csv", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")
    rows = _rows(resp.text)
    assert len(rows) > 800
    assert all(r["name"] == r["player_key"] for r in rows)


async def test_export_requires_auth(client: AsyncClient):
    assert (await client.get("/auth/me/player-names.csv")).status_code == 401


async def test_import_saves_only_changed_rows_and_export_reflects_them(
    client: AsyncClient, auth_headers: dict
):
    exported = (await client.get("/auth/me/player-names.csv", headers=auth_headers)).text
    key = _rows(exported)[0]["player_key"]

    resp = await client.post(
        "/auth/me/player-names.csv",
        json={"csv": _csv([(key, "My Chosen Name")])},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["renamed"] == 1

    again = _rows((await client.get("/auth/me/player-names.csv", headers=auth_headers)).text)
    assert {r["player_key"]: r["name"] for r in again}[key] == "My Chosen Name"


async def test_overrides_apply_to_a_career_created_afterwards(
    client: AsyncClient, auth_headers: dict
):
    """The whole point of the feature."""
    exported = (await client.get("/auth/me/player-names.csv", headers=auth_headers)).text
    # Pick a name that actually appears in a rosters2026 career.
    baseline = await _create_career(client, auth_headers, name="Baseline")
    in_career = sorted(_career_names(baseline))[0]
    assert in_career in {r["player_key"] for r in _rows(exported)}

    await client.post(
        "/auth/me/player-names.csv",
        json={"csv": _csv([(in_career, "Renamed By Settings")])},
        headers=auth_headers,
    )

    fresh = await _create_career(client, auth_headers, name="After Override")
    names = _career_names(fresh)
    assert "Renamed By Settings" in names
    assert in_career not in names


async def test_overrides_do_not_touch_careers_that_already_exist(
    client: AsyncClient, auth_headers: dict
):
    """Stated limitation, asserted so it cannot regress into a surprise.

    An existing career's names are baked into its saved lineups, leadership and
    archived scorecards; rewriting those is a per-career operation, not a
    settings toggle.
    """
    before = await _create_career(client, auth_headers, name="Existing")
    target = sorted(_career_names(before))[0]

    await client.post(
        "/auth/me/player-names.csv",
        json={"csv": _csv([(target, "Should Not Appear Here")])},
        headers=auth_headers,
    )

    reloaded = (await client.get(f"/careers/{before['id']}", headers=auth_headers)).json()
    names = _career_names(reloaded)
    assert target in names
    assert "Should Not Appear Here" not in names


async def test_invalid_file_is_rejected_with_every_error(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/auth/me/player-names.csv",
        json={"csv": _csv([("Nobody One", "A"), ("Nobody Two", "B")])},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert len(resp.json()["detail"]["errors"]) >= 2


async def test_overrides_are_per_user(client: AsyncClient, auth_headers: dict):
    exported = (await client.get("/auth/me/player-names.csv", headers=auth_headers)).text
    key = _rows(exported)[0]["player_key"]
    await client.post(
        "/auth/me/player-names.csv",
        json={"csv": _csv([(key, "Mine Only")])},
        headers=auth_headers,
    )

    other = await client.post("/auth/guest")
    other_headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}
    theirs = _rows((await client.get("/auth/me/player-names.csv", headers=other_headers)).text)
    assert {r["player_key"]: r["name"] for r in theirs}[key] == key


async def test_clearing_overrides_restores_shipped_names(client: AsyncClient, auth_headers: dict):
    exported = (await client.get("/auth/me/player-names.csv", headers=auth_headers)).text
    key = _rows(exported)[0]["player_key"]
    await client.post(
        "/auth/me/player-names.csv", json={"csv": _csv([(key, "Temporary")])}, headers=auth_headers
    )
    # Re-importing an unedited export is how a user undoes everything.
    resp = await client.post(
        "/auth/me/player-names.csv", json={"csv": _csv([(key, key)])}, headers=auth_headers
    )
    assert resp.json()["renamed"] == 0

    again = _rows((await client.get("/auth/me/player-names.csv", headers=auth_headers)).text)
    assert {r["player_key"]: r["name"] for r in again}[key] == key
