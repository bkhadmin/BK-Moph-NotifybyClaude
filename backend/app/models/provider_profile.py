from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ProviderProfile(Base):
    __tablename__='provider_profiles'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    user_id:Mapped[int|None]=mapped_column(nullable=True)
    account_id:Mapped[str|None]=mapped_column(String(100), nullable=True)
    provider_id:Mapped[str|None]=mapped_column(String(100), nullable=True)
    hash_cid:Mapped[str|None]=mapped_column(String(255), nullable=True)
    title_name:Mapped[str|None]=mapped_column(String(100), nullable=True)
    name_th:Mapped[str|None]=mapped_column(String(255), nullable=True)
    first_name:Mapped[str|None]=mapped_column(String(255), nullable=True)
    last_name:Mapped[str|None]=mapped_column(String(255), nullable=True)
    position_name:Mapped[str|None]=mapped_column(String(255), nullable=True)
    organization_name:Mapped[str|None]=mapped_column(String(255), nullable=True)
    organization_code:Mapped[str|None]=mapped_column(String(100), nullable=True)
    license_no:Mapped[str|None]=mapped_column(String(100), nullable=True)
    phone:Mapped[str|None]=mapped_column(String(100), nullable=True)
    email:Mapped[str|None]=mapped_column(String(255), nullable=True)
    raw_json:Mapped[str|None]=mapped_column(Text, nullable=True)
