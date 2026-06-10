import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PlayerDatasetEntry(Base):
    """Master player datasets (current era, all-time greats, future content
    packs like international rosters), seeded once and queried at draft init
    instead of loading CSVs at runtime.
    """

    __tablename__ = "player_dataset_pool"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_type: Mapped[str] = mapped_column(String, nullable=False)  # 'current' | 'alltime' | 'international_t20' | ...
    name: Mapped[str] = mapped_column(String, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False)
