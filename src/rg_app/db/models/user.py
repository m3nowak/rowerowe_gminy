from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from rg_app.db.models.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    access_token: Mapped[str] = mapped_column(String(40))
    refresh_token: Mapped[str] = mapped_column(String(40))
    expires_at: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(255))
