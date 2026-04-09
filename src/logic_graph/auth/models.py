from typing import Optional

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from logic_graph.db.base import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)
