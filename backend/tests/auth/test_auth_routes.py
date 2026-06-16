from httpx import AsyncClient

from app.auth.providers.apple import AppleIdentity, AppleTokenError
from app.auth.providers.google import GoogleIdentity, GoogleTokenError


async def _create_guest(client: AsyncClient) -> dict:
    resp = await client.post("/auth/guest")
    assert resp.status_code == 200
    return resp.json()


async def test_guest_signup_returns_tokens_and_user(client: AsyncClient):
    body = await _create_guest(client)

    assert body["user"]["email"] is None
    assert body["user"]["has_apple_link"] is False
    assert body["user"]["has_google_link"] is False
    assert body["tokens"]["token_type"] == "bearer"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


async def test_me_requires_access_token(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user(client: AsyncClient):
    body = await _create_guest(client)
    access_token = body["tokens"]["access_token"]

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == body["user"]["id"]


async def test_refresh_rotates_tokens(client: AsyncClient):
    body = await _create_guest(client)
    old_refresh = body["tokens"]["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["refresh_token"] != old_refresh

    # Old refresh token is now revoked.
    resp = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401


async def test_refresh_with_invalid_token_rejected(client: AsyncClient):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


async def test_delete_account_requires_auth(client: AsyncClient):
    resp = await client.delete("/auth/me")
    assert resp.status_code == 401


async def test_delete_account_removes_user_and_revokes_session(client: AsyncClient):
    body = await _create_guest(client)
    headers = {"Authorization": f"Bearer {body['tokens']['access_token']}"}

    resp = await client.delete("/auth/me", headers=headers)
    assert resp.status_code == 204

    # The user is gone: their access token no longer resolves to a user...
    assert (await client.get("/auth/me", headers=headers)).status_code == 401
    # ...and their refresh token can't mint a new session.
    refresh = await client.post("/auth/refresh", json={"refresh_token": body["tokens"]["refresh_token"]})
    assert refresh.status_code == 401


async def test_delete_account_cascades_to_careers(client: AsyncClient):
    body = await _create_guest(client)
    headers = {"Authorization": f"Bearer {body['tokens']['access_token']}"}
    create = await client.post(
        "/careers",
        json={
            "name": "Doomed Career",
            "user_team_name": "Mumbai Mavericks",
            "difficulty": "medium",
            "draft_pool_type": "rosters2026",
        },
        headers=headers,
    )
    assert create.status_code == 200, create.text

    assert (await client.delete("/auth/me", headers=headers)).status_code == 204

    # The careers list now errors (user gone) — the career was cascade-deleted,
    # not orphaned.
    assert (await client.get("/careers", headers=headers)).status_code == 401


async def test_apple_sign_in_creates_new_user(client: AsyncClient, monkeypatch):
    async def fake_verify(identity_token: str):
        return AppleIdentity(sub="apple-sub-123", email="player@example.com")

    monkeypatch.setattr("app.auth.router.verify_apple_identity_token", fake_verify)

    resp = await client.post("/auth/apple", json={"identity_token": "fake", "display_name": "Akshay"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "player@example.com"
    assert body["user"]["has_apple_link"] is True


async def test_apple_sign_in_reuses_existing_user(client: AsyncClient, monkeypatch):
    async def fake_verify(identity_token: str):
        return AppleIdentity(sub="apple-sub-456", email="repeat@example.com")

    monkeypatch.setattr("app.auth.router.verify_apple_identity_token", fake_verify)

    first = await client.post("/auth/apple", json={"identity_token": "fake"})
    second = await client.post("/auth/apple", json={"identity_token": "fake"})

    assert first.json()["user"]["id"] == second.json()["user"]["id"]


async def test_apple_sign_in_invalid_token_rejected(client: AsyncClient, monkeypatch):
    async def fake_verify(identity_token: str):
        raise AppleTokenError("bad token")

    monkeypatch.setattr("app.auth.router.verify_apple_identity_token", fake_verify)

    resp = await client.post("/auth/apple", json={"identity_token": "fake"})
    assert resp.status_code == 401


async def test_google_sign_in_creates_new_user(client: AsyncClient, monkeypatch):
    async def fake_verify(id_token: str):
        return GoogleIdentity(sub="google-sub-123", email="googler@example.com")

    monkeypatch.setattr("app.auth.router.verify_google_id_token", fake_verify)

    resp = await client.post("/auth/google", json={"id_token": "fake", "display_name": "Akshay"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "googler@example.com"
    assert body["user"]["has_google_link"] is True


async def test_google_sign_in_invalid_token_rejected(client: AsyncClient, monkeypatch):
    async def fake_verify(id_token: str):
        raise GoogleTokenError("bad token")

    monkeypatch.setattr("app.auth.router.verify_google_id_token", fake_verify)

    resp = await client.post("/auth/google", json={"id_token": "fake"})
    assert resp.status_code == 401


async def test_link_apple_account_to_guest(client: AsyncClient, monkeypatch):
    guest = await _create_guest(client)
    access_token = guest["tokens"]["access_token"]

    async def fake_verify(identity_token: str):
        return AppleIdentity(sub="apple-sub-link", email="linked@example.com")

    monkeypatch.setattr("app.auth.router.verify_apple_identity_token", fake_verify)

    resp = await client.post(
        "/auth/link/apple",
        json={"identity_token": "fake"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_apple_link"] is True
    assert body["email"] == "linked@example.com"
    assert body["id"] == guest["user"]["id"]


async def test_link_apple_account_already_linked_to_other_user(client: AsyncClient, monkeypatch):
    async def fake_verify(identity_token: str):
        return AppleIdentity(sub="apple-sub-taken", email="taken@example.com")

    monkeypatch.setattr("app.auth.router.verify_apple_identity_token", fake_verify)

    # First user signs in with Apple, claiming this apple_sub.
    await client.post("/auth/apple", json={"identity_token": "fake"})

    # A second guest tries to link the same Apple account.
    guest = await _create_guest(client)
    access_token = guest["tokens"]["access_token"]

    resp = await client.post(
        "/auth/link/apple",
        json={"identity_token": "fake"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 409


async def test_link_google_account_to_guest(client: AsyncClient, monkeypatch):
    guest = await _create_guest(client)
    access_token = guest["tokens"]["access_token"]

    async def fake_verify(id_token: str):
        return GoogleIdentity(sub="google-sub-link", email="glinked@example.com")

    monkeypatch.setattr("app.auth.router.verify_google_id_token", fake_verify)

    resp = await client.post(
        "/auth/link/google",
        json={"id_token": "fake"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_google_link"] is True
    assert body["email"] == "glinked@example.com"


async def test_invalid_access_token_rejected(client: AsyncClient):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert resp.status_code == 401
