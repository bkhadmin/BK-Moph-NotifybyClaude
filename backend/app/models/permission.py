from sqlalchemy import String
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class Permission(Base):
    __tablename__='permissions'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    code:Mapped[str]=mapped_column(String(100), unique=True, nullable=False)
    name:Mapped[str]=mapped_column(String(150), nullable=False)
