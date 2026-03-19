from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ProviderProfileHistory(Base):
    __tablename__='provider_profile_histories'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    provider_profile_id:Mapped[int|None]=mapped_column(nullable=True)
    action:Mapped[str]=mapped_column(String(50), nullable=False)
    changed_by:Mapped[str|None]=mapped_column(String(100), nullable=True)
    before_json:Mapped[str|None]=mapped_column(Text, nullable=True)
    after_json:Mapped[str|None]=mapped_column(Text, nullable=True)
    diff_json:Mapped[str|None]=mapped_column(Text, nullable=True)
