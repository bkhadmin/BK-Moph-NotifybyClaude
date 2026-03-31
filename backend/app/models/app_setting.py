from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AppSetting(Base):
    __tablename__ = 'app_settings'
    key:   Mapped[str]      = mapped_column(String(100), primary_key=True)
    value: Mapped[str|None] = mapped_column(Text, nullable=True)
