import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.careers.service import CareerNotFoundError
from app.db.models.user import User
from app.db.redis import get_redis
from app.db.session import get_db
from app.live_match import service as live_match_service
from app.live_match.service import LiveMatchError
from app.season import service
from app.season.schemas import (
    AutodraftRequest,
    DraftPickRequest,
    LeadershipRequest,
    PresetsRequest,
    RetentionRequest,
)

router = APIRouter(prefix="/careers/{career_id}", tags=["season"])


@router.get("/payload", response_model=dict)
async def get_payload(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    try:
        return await service.get_payload(db, redis, user.id, career_id)
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/draft/start", response_model=dict)
async def start_draft(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.start_draft(db, redis, user.id, career_id))


@router.post("/draft/pick", response_model=dict)
async def draft_pick(
    career_id: uuid.UUID,
    body: DraftPickRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.draft_pick(db, redis, user.id, career_id, body.player_name))


@router.post("/draft/autodraft", response_model=dict)
async def autodraft(
    career_id: uuid.UUID,
    body: AutodraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.autodraft(db, redis, user.id, career_id, body.mode))


@router.post("/leadership", response_model=dict)
async def set_leadership(
    career_id: uuid.UUID,
    body: LeadershipRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.set_leadership(db, redis, user.id, career_id, body.captain, body.vice, body.wicketkeeper))


@router.post("/presets", response_model=dict)
async def set_presets(
    career_id: uuid.UUID,
    body: PresetsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.set_presets(db, redis, user.id, career_id, body.model_dump()))


@router.post("/season/simulate-round", response_model=dict)
async def simulate_round(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(live_match_service.simulate_round(db, redis, user.id, career_id))


@router.post("/season/start-playoffs", response_model=dict)
async def start_playoffs(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.start_playoffs(db, redis, user.id, career_id))


@router.post("/retention/open", response_model=dict)
async def open_retention(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.open_retention(db, redis, user.id, career_id))


@router.post("/retention", response_model=dict)
async def submit_retentions(
    career_id: uuid.UUID,
    body: RetentionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    return await _run(service.submit_retentions(db, redis, user.id, career_id, body.players))


async def _run(coro) -> dict:
    try:
        return await coro
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (service.LiveMatchInProgressError, service.SeasonError, ValueError, LiveMatchError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
