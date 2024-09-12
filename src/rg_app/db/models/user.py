from datetime import datetime, UTC

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from rg_app.db.models.base import Base

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    access_token: Mapped[str] = mapped_column(String(40))
    refresh_token: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,  default=lambda: datetime.now(UTC), server_default=func.now()
    )
    last_login: Mapped[datetime] = mapped_column(
        DateTime,  default=lambda: datetime.now(UTC), server_default=func.now()
    )
