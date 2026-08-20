import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.careers import service
from app.careers.schemas import (
    CareerCreateRequest,
    CareerDetail,
    CareerSummary,
    MatchBallOut,
    MatchBallsOut,
    MatchDetail,
    MatchSummary,
)
from app.db.models.career import Career, Match, MatchBall
from app.db.models.user import User
from app.db.session import get_db
from cricket_sim_engine.sim.league_state import LeagueState

router = APIRouter(prefix="/careers", tags=["careers"])


def _summary(career: Career) -> CareerSummary:
    return CareerSummary(
        id=career.id,
        name=career.name,
        user_team_name=career.user_team_name,
        difficulty=career.difficulty,
        draft_pool_type=career.draft_pool_type,
        competition=getattr(career, "competition", "ipl"),
        match_format=getattr(career, "match_format", "t20"),
        career_mode=getattr(career, "career_mode", "league"),
        series_length=getattr(career, "series_length", None),
        phase=career.phase,
        season_year=career.season_year,
        completed_seasons=career.completed_seasons,
        status_message=career.status_message,
        created_at=career.created_at,
        updated_at=career.updated_at,
    )


def _detail(career: Career) -> CareerDetail:
    return CareerDetail(**_summary(career).model_dump(), state=career.state_blob)


def _match_summary(match: Match) -> MatchSummary:
    return MatchSummary(
        id=match.id,
        season_year=match.season_year,
        round_num=match.round_num,
        stage=match.stage,
        team1_name=match.team1_name,
        team2_name=match.team2_name,
        toss_winner=match.toss_winner,
        toss_decision=match.toss_decision,
        result_summary=match.result_summary,
        winner_name=match.winner_name,
        played_at=match.played_at,
    )


def _match_detail(match: Match, motm_player_name: str | None) -> MatchDetail:
    return MatchDetail(
        **_match_summary(match).model_dump(),
        team1_score=match.team1_score,
        team2_score=match.team2_score,
        motm_player_id=match.motm_player_id,
        motm_player_name=motm_player_name,
    )


def _match_ball_out(ball: MatchBall, names_by_id: dict) -> MatchBallOut:
    return MatchBallOut(
        innings=ball.innings,
        over_num=ball.over_num,
        ball_num=ball.ball_num,
        batter_id=ball.batter_id,
        batter_name=names_by_id.get(ball.batter_id),
        bowler_id=ball.bowler_id,
        bowler_name=names_by_id.get(ball.bowler_id),
        runs=ball.runs,
        extras=ball.extras,
        wicket=ball.wicket,
        commentary=ball.commentary,
    )


@router.post("", response_model=CareerDetail)
async def create_career(
    body: CareerCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CareerDetail:
    try:
        career = await service.create_career(
            db, user.id, body.name, body.user_team_name, body.difficulty, body.draft_pool_type,
            competition=body.competition, match_format=body.match_format,
            career_mode=body.career_mode, series_length=body.series_length,
            opponent_name=body.opponent_name,
        )
    except service.CareerError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    return _detail(career)


@router.get("", response_model=list[CareerSummary])
async def list_careers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CareerSummary]:
    careers = await service.list_careers(db, user.id)
    return [_summary(c) for c in careers]


@router.get("/{career_id}", response_model=CareerDetail)
async def get_career(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CareerDetail:
    try:
        career = await service.get_career(db, user.id, career_id)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return _detail(career)


@router.put("/{career_id}/state", response_model=CareerDetail)
async def save_career_state(
    career_id: uuid.UUID,
    body: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CareerDetail:
    """Persist a full career state blob (as produced by `LeagueState.to_dict()`)."""
    try:
        league = LeagueState.from_dict(body)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid career state: {exc}") from exc

    try:
        career = await service.save_league_state(db, user.id, career_id, league)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return _detail(career)


@router.delete("/{career_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_career(
    career_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await service.delete_career(db, user.id, career_id)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.get("/{career_id}/matches", response_model=list[MatchSummary])
async def list_matches(
    career_id: uuid.UUID,
    season_year: int | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MatchSummary]:
    try:
        matches = await service.list_matches(db, user.id, career_id, season_year)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return [_match_summary(m) for m in matches]


@router.get("/{career_id}/matches/{match_id}", response_model=MatchDetail)
async def get_match(
    career_id: uuid.UUID,
    match_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchDetail:
    try:
        match = await service.get_match(db, user.id, career_id, match_id)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.MatchNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    names_by_id = await service.player_names_by_id(db, career_id, {match.motm_player_id})
    return _match_detail(match, names_by_id.get(match.motm_player_id))


@router.get("/{career_id}/matches/{match_id}/balls", response_model=MatchBallsOut)
async def get_match_balls(
    career_id: uuid.UUID,
    match_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchBallsOut:
    try:
        balls = await service.get_match_balls(db, user.id, career_id, match_id)
    except service.CareerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except service.MatchNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    player_ids = {b.batter_id for b in balls} | {b.bowler_id for b in balls}
    names_by_id = await service.player_names_by_id(db, career_id, player_ids)
    return MatchBallsOut(match_id=match_id, balls=[_match_ball_out(b, names_by_id) for b in balls])
