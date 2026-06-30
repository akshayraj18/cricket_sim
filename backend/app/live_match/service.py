import hashlib
import hmac
import pickle
import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from cricket_sim_engine.sim.league_state import LeagueState

from app.careers import service as careers_service
from app.careers.service import CareerNotFoundError
from app.core.config import settings

LIVE_STATE_TTL_SECONDS = 24 * 60 * 60

# The live-match cache holds an in-progress LiveMatch, whose full ball-by-ball
# state LeagueState.to_dict() intentionally omits, so we serialise it with
# pickle. To make unpickling safe even if the Redis store is tampered with, each
# blob is prefixed with an HMAC-SHA256 signature keyed on JWT_SECRET; we refuse
# to unpickle any blob whose signature doesn't verify. This closes the
# "deserialization of untrusted data" risk: only blobs this process wrote (with
# the secret) are ever loaded.
_SIG_LEN = 32  # HMAC-SHA256 digest size in bytes


def _sign(blob: bytes) -> bytes:
    return hmac.new(settings.jwt_secret.encode(), blob, hashlib.sha256).digest()


class LiveMatchError(Exception):
    pass


class NoLiveMatchError(LiveMatchError):
    pass


def _redis_key(career_id: uuid.UUID) -> str:
    return f"career:{career_id}:live_state"


async def load_cached_state(redis: Redis, career_id: uuid.UUID) -> LeagueState | None:
    signed = await redis.get(_redis_key(career_id))
    if signed is None:
        return None
    signature, blob = signed[:_SIG_LEN], signed[_SIG_LEN:]
    # Only unpickle blobs we wrote (signature verifies against JWT_SECRET).
    # A tampered/forged blob is treated as no cached state, not deserialised.
    if not hmac.compare_digest(signature, _sign(blob)):
        return None
    return pickle.loads(blob)  # nosec B301 - integrity verified by HMAC above


async def _save_live_state(redis: Redis, career_id: uuid.UUID, league: LeagueState) -> None:
    blob = pickle.dumps(league)
    await redis.set(_redis_key(career_id), _sign(blob) + blob, ex=LIVE_STATE_TTL_SECONDS)


async def _clear_live_state(redis: Redis, career_id: uuid.UUID) -> None:
    await redis.delete(_redis_key(career_id))


async def has_live_match(redis: Redis, career_id: uuid.UUID) -> bool:
    """Whether an interactive live match is currently cached for `career_id`."""
    return await redis.exists(_redis_key(career_id)) == 1


async def get_live_match(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID
) -> dict:
    """The current live match payload for `career_id`, or raise `NoLiveMatchError` if none is in progress."""
    await careers_service.get_career(db, user_id, career_id)  # ownership check, 404 if missing

    league = await load_cached_state(redis, career_id)
    if league is None or league.live_match is None:
        raise NoLiveMatchError("No live match in progress.")
    return league.live_match.payload()


async def begin_match(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID
) -> dict:
    """Start the next match day for `career_id` and cache the resulting `LeagueState` in Redis."""
    league = await careers_service.load_league_state(db, user_id, career_id)

    league.begin_match_day(interactive=True)
    if league.live_match is None:
        raise LiveMatchError("No interactive match was started for this round.")

    await _save_live_state(redis, career_id, league)
    return league.live_match.payload()


async def apply_action(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID, action: str, body: dict
) -> dict:
    """Apply a live-match action to the cached `LeagueState` for `career_id` and re-cache it."""
    await careers_service.get_career(db, user_id, career_id)  # ownership check, 404 if missing

    league = await load_cached_state(redis, career_id)
    if league is None or league.live_match is None:
        raise NoLiveMatchError("No live match in progress.")

    match = league.live_match

    if action == "toss":
        match.choose_toss(body["decision"])
    elif action == "lineup":
        match.set_user_xi(
            body.get("xi", []),
            body.get("batting_order", []),
            body.get("bowling_order", []),
            body.get("intents", {}),
            body.get("save", False),
            body.get("context", "batting"),
            body.get("wicketkeeper", ""),
        )
    elif action == "play-over":
        match.play_over(body.get("bowler"), max_balls=int(body.get("balls", 6)), stop_on_wicket=body.get("stop_on_wicket", True))
    elif action == "play-ball":
        match.play_over(body.get("bowler"), max_balls=1, stop_on_wicket=True)
    elif action == "play-until":
        balls = int(body.get("balls", 6))
        while match.status == "over" and balls > 0:
            before = match.score["balls"]
            match.play_over(body.get("bowler"), max_balls=min(6, balls), stop_on_wicket=body.get("stop_on_wicket", True))
            balls -= max(1, match.score["balls"] - before)
            if body.get("stop_on_wicket", True) and match.score.get("last_event_wicket") and match.status != "over":
                break
            if match.status != "over":
                break
    elif action == "aggression":
        match.set_aggression(body.get("batting", {}), body.get("bowling", {}))
    elif action == "next-batter":
        match.select_next_batter(body.get("name", ""))
    elif action == "super-over-lineup":
        match.set_super_over_lineup(body.get("batters", []), body.get("bowler", ""))
    elif action == "impact-sub":
        match.apply_impact_sub(body.get("out"), body.get("in"))
    elif action == "proceed-session":
        match.proceed_session()
    elif action == "follow-on-decision":
        match.decide_follow_on(body.get("enforce", True))
    elif action == "declare":
        match.declare_innings()
    else:
        raise LiveMatchError(f"Unknown action: {action}")

    await _save_live_state(redis, career_id, league)
    return match.payload()


async def complete_match(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID
) -> dict:
    """Acknowledge the finished live match: persist the resulting `LeagueState` to Postgres and clear the Redis cache."""
    league = await load_cached_state(redis, career_id)
    if league is None or league.live_match is None:
        raise NoLiveMatchError("No live match in progress.")

    try:
        league.complete_live_match()
    except ValueError as exc:
        raise LiveMatchError(str(exc)) from exc

    try:
        career = await careers_service.save_league_state(db, user_id, career_id, league)
    except CareerNotFoundError:
        raise

    await _clear_live_state(redis, career_id)
    return {
        "phase": career.phase,
        "round_num": league.round_num,
        "season_year": career.season_year,
        "status_message": career.status_message,
    }


async def simulate_round(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID
) -> dict:
    """Quick-sim the rest of the current round (or playoff match), resolving any cached live match first.

    Persists the result to Postgres and clears any cached live-match state.
    """
    league = await load_cached_state(redis, career_id)
    if league is None:
        league = await careers_service.load_league_state(db, user_id, career_id)

    try:
        league.simulate_current_round()
    except ValueError as exc:
        raise LiveMatchError(str(exc)) from exc

    await careers_service.save_league_state(db, user_id, career_id, league)
    await _clear_live_state(redis, career_id)
    return league.payload()
