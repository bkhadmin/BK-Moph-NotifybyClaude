from sqlalchemy import String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class AccessLog(Base):
    __tablename__='access_logs'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    actor:Mapped[str|None]=mapped_column(String(100), nullable=True)
    ip_address:Mapped[str|None]=mapped_column(String(100), nullable=True)
    action:Mapped[str]=mapped_column(String(100), nullable=False)
    status:Mapped[str]=mapped_column(String(30), nullable=False)
    detail:Mapped[str|None]=mapped_column(Text, nullable=True)
