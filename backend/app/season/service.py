import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.careers import service as careers_service
from app.live_match.service import has_live_match, load_cached_state


class SeasonError(Exception):
    pass


class LiveMatchInProgressError(SeasonError):
    pass


async def _load_state(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID):
    """Load `career_id`'s persisted `LeagueState`, refusing if a live match is in progress.

    Season-level actions (draft, leadership, retention, playoffs) operate on
    the DB-persisted state and would conflict with an interactive match
    cached in Redis (see `app.live_match.service`). The user must complete or
    quick-sim that match first.
    """
    if await has_live_match(redis, career_id):
        raise LiveMatchInProgressError("Finish or quick-sim the current match before continuing.")
    return await careers_service.load_league_state(db, user_id, career_id)


async def _save_and_payload(db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID, league) -> dict:
    await careers_service.save_league_state(db, user_id, career_id, league)
    return league.payload()


async def start_draft(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.start_draft()
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def draft_pick(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID, player_name: str) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.user_pick(player_name)
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def autodraft(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID, mode: str) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        if mode == "all":
            league.autodraft_to_end()
        else:
            league.autodraft_user_pick()
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def set_leadership(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID,
    captain_name: str, vice_name: str, wicketkeeper_name: str = "",
) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.set_leadership(captain_name, vice_name, wicketkeeper_name)
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def set_presets(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID, body: dict
) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.set_user_presets(
            body.get("batting_order", []),
            body.get("bowling_order", []),
            body.get("batting_first_xi"),
            body.get("bowling_first_xi"),
            body.get("bat_to_bowl"),
            body.get("bowl_to_bat"),
            body.get("wicketkeeper", ""),
        )
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def start_playoffs(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.start_playoffs()
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def open_retention(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.open_retention()
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def submit_retentions(
    db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID, player_names: list[str]
) -> dict:
    league = await _load_state(db, redis, user_id, career_id)
    try:
        league.submit_retentions(player_names)
    except ValueError as exc:
        raise SeasonError(str(exc)) from exc
    return await _save_and_payload(db, user_id, career_id, league)


async def get_payload(db: AsyncSession, redis: Redis, user_id: uuid.UUID, career_id: uuid.UUID) -> dict:
    """The full frontend-ready league payload, including the live match (if one is cached in Redis)."""
    await careers_service.get_career(db, user_id, career_id)  # ownership check, 404 if missing

    league = await load_cached_state(redis, career_id)
    if league is None:
        league = await careers_service.load_league_state(db, user_id, career_id)
    return league.payload()
