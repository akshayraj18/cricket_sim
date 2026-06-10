import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlayerSeasonStats(Base):
    """Per-season archived stats snapshot, so career-long leaderboards work
    without re-deriving from match logs.
    """

    __tablename__ = "player_season_stats"
    __table_args__ = (
        UniqueConstraint("career_id", "player_id", "season_year", name="uq_player_season_stats"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    career_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("careers.id", ondelete="CASCADE"))
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"))
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    team_name: Mapped[str | None] = mapped_column(String, nullable=True)
    stats: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mvp_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
