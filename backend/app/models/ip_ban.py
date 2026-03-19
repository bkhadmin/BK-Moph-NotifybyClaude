from sqlalchemy import String,Integer
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class IpBan(Base):
    __tablename__='ip_bans'
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    ip_address:Mapped[str]=mapped_column(String(100), unique=True, nullable=False)
    fail_count:Mapped[int]=mapped_column(Integer, default=0, nullable=False)
    is_banned:Mapped[str]=mapped_column(String(1), default='N', nullable=False)
