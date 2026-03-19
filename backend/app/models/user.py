from sqlalchemy import String,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class User(Base):
    __tablename__='users'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    username:Mapped[str]=mapped_column(String(100), unique=True, nullable=False)
    password_hash:Mapped[str|None]=mapped_column(String(255), nullable=True)
    display_name:Mapped[str|None]=mapped_column(String(255), nullable=True)
    auth_type:Mapped[str]=mapped_column(String(30), default='local', nullable=False)
    provider_account_id:Mapped[str|None]=mapped_column(String(100), nullable=True)
    provider_id:Mapped[str|None]=mapped_column(String(100), nullable=True)
    role_id:Mapped[int|None]=mapped_column(ForeignKey('roles.id'), nullable=True)
    profile_json:Mapped[str|None]=mapped_column(Text, nullable=True)
    is_active:Mapped[str]=mapped_column(String(1), default='Y', nullable=False)
