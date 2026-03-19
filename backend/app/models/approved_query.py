from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ApprovedQuery(Base):
    __tablename__='approved_queries'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    name:Mapped[str]=mapped_column(String(255), nullable=False)
    sql_text:Mapped[str]=mapped_column(Text, nullable=False)
    max_rows:Mapped[int]=mapped_column(Integer, default=100, nullable=False)
    is_active:Mapped[str]=mapped_column(String(1), default='Y', nullable=False)
