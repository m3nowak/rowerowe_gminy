from datetime import UTC, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rg_app.db.decorators import UTCDateTime

from .base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    access_token: Mapped[str] = mapped_column(String(40))
    refresh_token: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(UTC), server_default=func.now()
    )
    last_login: Mapped[datetime] = mapped_column(
        UTCDateTime, default=lambda: datetime.now(UTC), server_default=func.now()
    )
    last_backlog_sync: Mapped[datetime | None] = mapped_column(UTCDateTime, default=None, nullable=True)
    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="user")


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(String(255))
    manual: Mapped[bool] = mapped_column(Boolean)

    start: Mapped[datetime] = mapped_column(UTCDateTime)
    moving_time: Mapped[int] = mapped_column(BigInteger)
    elapsed_time: Mapped[int] = mapped_column(BigInteger)
    distance: Mapped[Decimal] = mapped_column(Numeric(8, 1))

    track: Mapped[str] = mapped_column(JSONB)
    track_is_detailed: Mapped[bool] = mapped_column(Boolean)

    elevation_gain: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 1), nullable=True)
    elevation_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    elevation_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)

    sport_type: Mapped[str] = mapped_column(String(32))
    gear_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    visited_regions: Mapped[list[str]] = mapped_column(JSONB)
    visited_regions_additional: Mapped[list[str]] = mapped_column(JSONB)

    user: Mapped[User] = relationship("User", back_populates="activities")


class Region(Base):
    __tablename__ = "region"

    id: Mapped[int] = mapped_column(String(16), primary_key=True)
    type: Mapped[str] = mapped_column(String(8), index=True)
    ancestors: Mapped[list[str]] = mapped_column(ARRAY(String(16), dimensions=1))
