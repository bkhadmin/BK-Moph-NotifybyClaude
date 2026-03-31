from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.services.timezone_write import bangkok_now_naive


class AlertTypeConfig(Base):
    __tablename__ = "alert_type_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bubble_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bubble_title_color: Mapped[str | None] = mapped_column(String(20), nullable=True, default="#b91c1c")
    # JSON arrays stored as text
    required_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_fields: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON object: standard_name -> query_column_name
    # standard names: patient_hn, patient_name, department, item_name, item_value,
    #                 report_date, report_time, doctor
    field_map: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON array of display lines in the bubble: [{"text": "ชื่อยา {drug_name}", "color": "#dc2626", "bold": true}]
    # ถ้าไม่ set จะใช้ default: item_name = item_value บรรทัดเดียว
    display_lines: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Template ข้อความตอบกลับหลังรับเคส — ใช้ {patient_name}, {item_name}, {item_value}, {claimed_by}, {claimed_at} ฯลฯ
    claim_notify_type: Mapped[str] = mapped_column(String(10), nullable=False, default='text')  # 'text' or 'flex'
    claim_notify_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[str] = mapped_column(String(1), default='Y', nullable=False)
    created_at: Mapped[object | None] = mapped_column(DateTime, nullable=False, default=bangkok_now_naive)
    updated_at: Mapped[object | None] = mapped_column(DateTime, nullable=False, default=bangkok_now_naive)