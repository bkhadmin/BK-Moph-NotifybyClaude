from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.base import Base
from app.services.timezone_utils import utcnow

class NotifyRoom(Base):
    __tablename__ = "notify_rooms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True)
    room_code = Column(String(80), nullable=True, unique=True)
    client_key = Column(Text, nullable=False)
    secret_key = Column(Text, nullable=False)
    is_active = Column(String(1), nullable=False, default="Y")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
