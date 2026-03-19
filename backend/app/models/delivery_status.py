from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class DeliveryStatus(Base):
    __tablename__='delivery_statuses'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    send_log_id:Mapped[int|None]=mapped_column(nullable=True)
    external_message_id:Mapped[str|None]=mapped_column(String(255), nullable=True)
    status:Mapped[str]=mapped_column(String(50), nullable=False)
    provider_status:Mapped[str|None]=mapped_column(String(100), nullable=True)
    detail:Mapped[str|None]=mapped_column(Text, nullable=True)
