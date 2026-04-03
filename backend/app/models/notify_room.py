from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base
from app.services.timezone_write import bangkok_now_naive

class NotifyRoom(Base):
    __tablename__ = "notify_rooms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True)
    room_code = Column(String(80), nullable=True, unique=True)
    channel_type = Column(String(20), nullable=False, default="moph_notify")  # moph_notify | telegram
    client_key = Column(Text, nullable=False)
    secret_key = Column(Text, nullable=True)
    is_active = Column(String(1), nullable=False, default="Y")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=bangkok_now_naive)
    updated_at = Column(DateTime, default=bangkok_now_naive, onupdate=bangkok_now_naive)
