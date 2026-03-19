from sqlalchemy import String,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class Role(Base):
    __tablename__='roles'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    code:Mapped[str]=mapped_column(String(50), unique=True, nullable=False)
    name:Mapped[str]=mapped_column(String(100), nullable=False)
    is_system:Mapped[bool]=mapped_column(Boolean, default=True, nullable=False)
