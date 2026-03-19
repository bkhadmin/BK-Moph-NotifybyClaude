from sqlalchemy.orm import Session
from app.models.role_permission import RolePermission
from app.models.permission import Permission
def get_permission_codes_for_role(db:Session, role_id:int):
    rows=db.query(Permission.code).join(RolePermission, RolePermission.permission_id==Permission.id).filter(RolePermission.role_id==role_id).all()
    return {r[0] for r in rows}
def set_role_permissions(db:Session, role_id:int, permission_ids:list[int]):
    db.query(RolePermission).filter(RolePermission.role_id==role_id).delete()
    for pid in permission_ids:
        db.add(RolePermission(role_id=role_id, permission_id=pid))
    db.commit()
