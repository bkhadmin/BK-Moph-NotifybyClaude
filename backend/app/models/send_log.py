from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.services.timezone_write import bangkok_now_naive

class SendLog(Base):
    __tablename__='send_logs'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    actor:Mapped[str|None]=mapped_column(String(100), nullable=True)
    channel:Mapped[str]=mapped_column(String(50), default='moph_notify', nullable=False)
    status:Mapped[str]=mapped_column(String(30), nullable=False)
    request_payload:Mapped[str|None]=mapped_column(Text, nullable=True)
    response_payload:Mapped[str|None]=mapped_column(Text, nullable=True)
    detail:Mapped[str|None]=mapped_column(Text, nullable=True)
    retry_count:Mapped[int]=mapped_column(Integer, default=0, nullable=False)
    created_at:Mapped[object|None]=mapped_column(DateTime, nullable=True, default=bangkok_now_naive)
