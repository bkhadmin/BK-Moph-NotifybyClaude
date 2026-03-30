from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.services.timezone_write import bangkok_now_naive

class AccessLog(Base):
    __tablename__='access_logs'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    actor:Mapped[str|None]=mapped_column(String(100), nullable=True)
    ip_address:Mapped[str|None]=mapped_column(String(100), nullable=True)
    action:Mapped[str]=mapped_column(String(100), nullable=False)
    status:Mapped[str]=mapped_column(String(30), nullable=False)
    detail:Mapped[str|None]=mapped_column(Text, nullable=True)
    created_at:Mapped[object|None]=mapped_column(DateTime, nullable=True, default=bangkok_now_naive)
