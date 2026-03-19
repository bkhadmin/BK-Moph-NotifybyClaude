from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.base import Base
from datetime import datetime

class ScheduleJobLog(Base):
    __tablename__ = "schedule_job_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_job_id = Column(Integer, ForeignKey("schedule_jobs.id"), nullable=False)
    run_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(20), nullable=False)
    rows_returned = Column(Integer, nullable=True)
    sent_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    detail_json = Column(Text, nullable=True)
