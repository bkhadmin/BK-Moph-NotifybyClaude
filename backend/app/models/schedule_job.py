from sqlalchemy import String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ScheduleJob(Base):
    __tablename__='schedule_jobs'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    name:Mapped[str]=mapped_column(String(255), nullable=False)
    schedule_type:Mapped[str]=mapped_column(String(30), nullable=False)
    cron_value:Mapped[str|None]=mapped_column(String(100), nullable=True)
    interval_minutes:Mapped[int|None]=mapped_column(Integer, nullable=True)
    approved_query_id:Mapped[int|None]=mapped_column(Integer, nullable=True)
    message_template_id:Mapped[int|None]=mapped_column(Integer, nullable=True)
    next_run_at:Mapped[object|None]=mapped_column(DateTime, nullable=True)
    last_run_at:Mapped[object|None]=mapped_column(DateTime, nullable=True)
    is_active:Mapped[str]=mapped_column(String(1), default='Y', nullable=False)
    payload_json:Mapped[str|None]=mapped_column(Text, nullable=True)
