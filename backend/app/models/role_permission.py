from sqlalchemy import ForeignKey,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base
class RolePermission(Base):
    __tablename__='role_permissions'
    __table_args__=(UniqueConstraint('role_id','permission_id',name='uq_role_permission'),)
    id:Mapped[int]=mapped_column(primary_key=True, autoincrement=True)
    role_id:Mapped[int]=mapped_column(ForeignKey('roles.id'), nullable=False)
    permission_id:Mapped[int]=mapped_column(ForeignKey('permissions.id'), nullable=False)
