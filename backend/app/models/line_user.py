from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base
from app.services.timezone_write import bangkok_now_naive

class LineUser(Base):
    __tablename__ = "line_users"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    line_uid    = Column(String(64), nullable=False, unique=True)   # LINE userId
    display_name = Column(String(200), nullable=True)               # LINE displayName
    real_name   = Column(String(200), nullable=True)                # ชื่อจริงที่ผูกไว้
    created_at  = Column(DateTime, default=bangkok_now_naive)
    updated_at  = Column(DateTime, default=bangkok_now_naive, onupdate=bangkok_now_naive)
