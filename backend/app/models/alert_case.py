from datetime import datetime
from app.services.timezone_utils import utcnow
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AlertCase(Base):
    __tablename__ = "alert_cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, default="lab_critical")
    patient_hn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    report_date_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    report_time_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    claimed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claimed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    first_sent_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    last_sent_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_row_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=False, default=utcnow)
