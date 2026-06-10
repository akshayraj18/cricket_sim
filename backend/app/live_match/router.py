import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.careers.service import CareerError, CareerNotFoundError
from app.db.models.user import User
from app.db.redis import get_redis
from app.db.session import get_db
from app.live_match import service
from app.live_match.schemas import MatchCompleteResponse

router = APIRouter(prefix="/careers/{career_id}/match", tags=["live-match"])

ACTIONS = (
    "toss",
    "lineup",
    "play-over",
    "play-ball",
    "play-until",
    "aggression",
    "next-batter",
    "super-over-lineup",
    "impact-sub",
)


@router.get("", response_model=dict)
async def get_live_match(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    try:
        return await service.get_live_match(db, redis, user.id, career_id)
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.NoLiveMatchError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/begin", response_model=dict)
async def begin_match(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    try:
        return await service.begin_match(db, redis, user.id, career_id)
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (CareerError, service.LiveMatchError, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.post("/complete", response_model=MatchCompleteResponse)
async def complete_match(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> MatchCompleteResponse:
    try:
        result = await service.complete_match(db, redis, user.id, career_id)
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.NoLiveMatchError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.LiveMatchError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return MatchCompleteResponse(**result)


@router.post("/{action}", response_model=dict)
async def apply_match_action(
    career_id: uuid.UUID,
    action: str,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    if action not in ACTIONS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown match action.")

    try:
        return await service.apply_action(db, redis, user.id, career_id, action, body)
    except CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.NoLiveMatchError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except (service.LiveMatchError, ValueError, KeyError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
