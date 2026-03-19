from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class MediaFile(Base):
    __tablename__='media_files'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    original_name:Mapped[str]=mapped_column(String(255), nullable=False)
    stored_name:Mapped[str]=mapped_column(String(255), nullable=False)
    mime_type:Mapped[str|None]=mapped_column(String(100), nullable=True)
    width:Mapped[int|None]=mapped_column(Integer, nullable=True)
    height:Mapped[int|None]=mapped_column(Integer, nullable=True)
    public_url:Mapped[str]=mapped_column(String(255), nullable=False)
