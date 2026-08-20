import uuid
from datetime import datetime

from pydantic import BaseModel


class CareerCreateRequest(BaseModel):
    name: str
    user_team_name: str
    difficulty: str = "medium"
    draft_pool_type: str = "rosters2026"  # "rosters2026" | "current" | "alltime" | "international_current"
    competition: str = "ipl"             # "ipl" | "international"
    match_format: str = "t20"            # "t20" | "odi" | "test"
    career_mode: str = "league"          # "league" | "tournament" | "bilateral"
    series_length: int | None = None     # 1 | 3 | 5 (bilateral only)
    opponent_name: str | None = None     # bilateral opponent


class CareerSummary(BaseModel):
    id: uuid.UUID
    name: str
    user_team_name: str
    difficulty: str
    draft_pool_type: str
    competition: str
    match_format: str
    career_mode: str
    series_length: int | None
    phase: str
    season_year: int
    completed_seasons: int
    status_message: str | None
    created_at: datetime
    updated_at: datetime


class CareerDetail(CareerSummary):
    state: dict


class MatchSummary(BaseModel):
    id: uuid.UUID
    season_year: int
    round_num: int | None
    stage: str
    team1_name: str
    team2_name: str
    toss_winner: str | None
    toss_decision: str | None
    result_summary: str | None
    winner_name: str | None
    played_at: datetime


class MatchDetail(MatchSummary):
    team1_score: dict | None
    team2_score: dict | None
    motm_player_id: uuid.UUID | None
    motm_player_name: str | None


class MatchBallOut(BaseModel):
    innings: int
    over_num: int
    ball_num: int
    batter_id: uuid.UUID | None
    batter_name: str | None
    bowler_id: uuid.UUID | None
    bowler_name: str | None
    runs: int
    extras: dict | None
    wicket: dict | None
    commentary: str | None


class MatchBallsOut(BaseModel):
    match_id: uuid.UUID
    balls: list[MatchBallOut]

