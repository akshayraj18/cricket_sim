"""The live-match Redis cache pickles in-progress match state, so each blob is
HMAC-signed with JWT_SECRET and only unpickled if the signature verifies. These
tests guard that integrity check: a legit round-trip loads, a tampered blob is
rejected (treated as no cached state) rather than deserialised.
"""
import pickle
import uuid

from redis.asyncio import from_url

from app.core.config import settings
from app.live_match import service as live_service

TEST_REDIS_URL = settings.redis_url.rsplit("/", 1)[0] + "/15"


async def test_signed_round_trip_loads():
    redis = from_url(TEST_REDIS_URL)
    career_id = uuid.uuid4()
    # A blank league is enough for a cache-layer round trip.
    from cricket_sim_engine.sim.league_state import LeagueState

    league = LeagueState()
    league.new_league("Mumbai Mavericks", "medium")
    try:
        await live_service._save_live_state(redis, career_id, league)
        loaded = await live_service.load_cached_state(redis, career_id)
        assert loaded is not None
        assert loaded.user_team_name == "Mumbai Mavericks"
    finally:
        await redis.delete(live_service._redis_key(career_id))
        await redis.aclose()


async def test_tampered_blob_is_rejected_not_unpickled():
    redis = from_url(TEST_REDIS_URL)
    career_id = uuid.uuid4()
    try:
        # Write an UNSIGNED pickle directly (simulating a tampered/forged blob
        # an attacker might place in Redis). load_cached_state must refuse it.
        forged = pickle.dumps({"malicious": "payload"})
        await redis.set(live_service._redis_key(career_id), forged)
        assert await live_service.load_cached_state(redis, career_id) is None

        # A blob signed with the WRONG key must also be rejected.
        import hashlib
        import hmac

        bad_sig = hmac.new(b"not-the-real-secret", forged, hashlib.sha256).digest()
        await redis.set(live_service._redis_key(career_id), bad_sig + forged)
        assert await live_service.load_cached_state(redis, career_id) is None
    finally:
        await redis.delete(live_service._redis_key(career_id))
        await redis.aclose()
