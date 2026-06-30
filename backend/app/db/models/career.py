import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Career(Base):
    __tablename__ = "careers"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_careers_user_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_team_name: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    draft_pool_type: Mapped[str] = mapped_column(String, nullable=False)
    competition: Mapped[str] = mapped_column(String, nullable=False, server_default="ipl")
    match_format: Mapped[str] = mapped_column(String, nullable=False, server_default="t20")
    career_mode: Mapped[str] = mapped_column(String, nullable=False, server_default="league")
    series_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase: Mapped[str] = mapped_column(String, nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_seasons: Mapped[int] = mapped_column(Integer, default=0)
    retention_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_message: Mapped[str | None] = mapped_column(String, nullable=True)

    # Working state: draft progress, schedule, playoff bracket, saved UI presets,
    # and any other transient/frequently-reshaped state not worth normalizing.
    state_blob: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("career_id", "name", name="uq_teams_career_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("careers.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_user_team: Mapped[bool] = mapped_column(default=False)

    points: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    runs_scored: Mapped[int] = mapped_column(Integer, default=0)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, default=0)

    captain_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vice_captain_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    saved_presets: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("careers.id", ondelete="CASCADE"))
    team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    base_ovr: Mapped[int] = mapped_column(Integer)
    batting_ovr: Mapped[int] = mapped_column(Integer)
    bowling_ovr: Mapped[int] = mapped_column(Integer)
    is_overseas: Mapped[bool] = mapped_column(default=False)
    age: Mapped[int] = mapped_column(Integer)
    batting_hand: Mapped[str] = mapped_column(String, default="Right")
    bowling_hand: Mapped[str] = mapped_column(String, default="Right")
    batting_archetype: Mapped[str] = mapped_column(String, default="Strike Rotator")
    bowling_phase: Mapped[str] = mapped_column(String, default="Flexible")
    bowling_type: Mapped[str] = mapped_column(String, default="None")
    strengths: Mapped[str | None] = mapped_column(String, nullable=True)
    weaknesses: Mapped[str | None] = mapped_column(String, nullable=True)
    preferred_position: Mapped[int] = mapped_column(Integer, default=6)

    form: Mapped[float] = mapped_column(default=5)
    intent: Mapped[str] = mapped_column(String, default="Normal")

    # season-to-date stats (reset each season, archived to player_season_stats)
    season_stats: Mapped[dict] = mapped_column(JSONB, default=dict)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("careers.id", ondelete="CASCADE"))
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    round_num: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String, nullable=False)  # league|qualifier1|eliminator|qualifier2|final|super_over

    team1_name: Mapped[str] = mapped_column(String, nullable=False)
    team2_name: Mapped[str] = mapped_column(String, nullable=False)
    toss_winner: Mapped[str | None] = mapped_column(String, nullable=True)
    toss_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(String, nullable=True)
    winner_name: Mapped[str | None] = mapped_column(String, nullable=True)

    team1_score: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    team2_score: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    motm_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    played_at: Mapped[datetime] = mapped_column(server_default=func.now())


class MatchBall(Base):
    """Ball-by-ball log for replay/commentary features.

    Deferred: not written to in Phase 0. Schema is created now so the live
    match WebSocket can start persisting balls in a later phase without a
    migration.
    """

    __tablename__ = "match_balls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id", ondelete="CASCADE"))
    innings: Mapped[int] = mapped_column(Integer, nullable=False)
    over_num: Mapped[int] = mapped_column(Integer, nullable=False)
    ball_num: Mapped[int] = mapped_column(Integer, nullable=False)
    batter_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    bowler_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    runs: Mapped[int] = mapped_column(Integer, default=0)
    extras: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    wicket: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    commentary: Mapped[str | None] = mapped_column(String, nullable=True)


class SeasonHistory(Base):
    __tablename__ = "season_history"
    __table_args__ = (UniqueConstraint("career_id", "season_year", name="uq_season_history_career_year"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("careers.id", ondelete="CASCADE"))
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    champion: Mapped[str | None] = mapped_column(String, nullable=True)
    runner_up: Mapped[str | None] = mapped_column(String, nullable=True)
    mvp_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    points_table: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    batting_leaderboard: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    bowling_leaderboard: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    playoff_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
