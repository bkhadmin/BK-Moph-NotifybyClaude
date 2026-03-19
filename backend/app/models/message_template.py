from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class MessageTemplate(Base):
    __tablename__='message_templates'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    name:Mapped[str]=mapped_column(String(255), nullable=False)
    template_type:Mapped[str]=mapped_column(String(30), default='text', nullable=False)
    content:Mapped[str]=mapped_column(Text, nullable=False)
    alt_text:Mapped[str|None]=mapped_column(String(255), nullable=True)
    is_active:Mapped[str]=mapped_column(String(1), default='Y', nullable=False)
