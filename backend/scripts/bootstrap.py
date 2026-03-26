from app.repositories.permissions import ensure_module53_permissions
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models import Role, Permission, Menu, User, AlertCase
from app.core.config import settings
from app.core.security import hash_password

ROLES=[('superadmin','Super Admin'),('admin1','Admin 1'),('admin2','Admin 2'),('user','User')]
PERMISSIONS=[
    ('menu.dashboard','Dashboard'),
    ('menu.users','User Management'),
    ('menu.messages','Message Management'),
    ('menu.logs','Logs'),
    ('menu.rbac','RBAC Management'),
    ('menu.notify','MOPH Notify'),
    ('menu.queries','Approved Query'),
    ('menu.templates','Message Templates'),
    ('menu.schedules','Schedules'),
    ('menu.media','Media Library'),
]
MENUS=[
    ('dashboard','Dashboard','/dashboard'),
    ('users','Users','/users'),
    ('logs','Logs','/logs/access'),
    ('rbac','RBAC','/rbac'),
    ('notify','MOPH Notify','/notify/test'),
    ('queries','Approved Queries','/queries'),
    ('templates','Templates','/templates'),
    ('schedules','Schedules','/schedules'),
    ('media','Media Library','/media'),
]
ROLE_PERMS={
    'superadmin':{'menu.dashboard','menu.users','menu.messages','menu.logs','menu.rbac','menu.notify','menu.queries','menu.templates','menu.schedules','menu.media'},
    'admin1':{'menu.dashboard','menu.users','menu.messages','menu.logs','menu.notify','menu.queries','menu.templates','menu.schedules','menu.media'},
    'admin2':{'menu.dashboard','menu.messages','menu.logs','menu.notify','menu.queries','menu.templates','menu.media'},
    'user':{'menu.dashboard','menu.queries','menu.templates'}
}


def ensure_module59_schema():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE schedule_jobs ADD COLUMN notify_room_id INT NULL"))
        except Exception:
            pass

def seed():
    Base.metadata.create_all(bind=engine)
    ensure_module59_schema()
    db:Session=SessionLocal()
    try:
        role_map={}
        for code,name in ROLES:
            row=db.query(Role).filter(Role.code==code).first()
            if not row:
                row=Role(code=code,name=name,is_system=True); db.add(row); db.flush()
            role_map[code]=row
        perm_map={}
        for code,name in PERMISSIONS:
            row=db.query(Permission).filter(Permission.code==code).first()
            if not row:
                row=Permission(code=code,name=name); db.add(row); db.flush()
            perm_map[code]=row
        for code,name,path in MENUS:
            if not db.query(Menu).filter(Menu.code==code).first():
                db.add(Menu(code=code,name=name,path=path))
        ensure_module53_permissions(db)
        db.commit()
        db.execute(text('DELETE FROM role_permissions'))
        for role_code, perm_codes in ROLE_PERMS.items():
            for perm_code in perm_codes:
                db.execute(text('INSERT INTO role_permissions (role_id, permission_id) VALUES (:rid,:pid)'), {'rid':role_map[role_code].id,'pid':perm_map[perm_code].id})
        user=db.query(User).filter(User.username==settings.internal_superadmin_username).first()
        if not user:
            db.add(User(username=settings.internal_superadmin_username,password_hash=hash_password(settings.internal_superadmin_password),display_name='Super Admin',auth_type='local',role_id=role_map['superadmin'].id))
        db.commit()
    finally:
        db.close()

if __name__=='__main__':
    seed()


from sqlalchemy import text

def ensure_module59_schema():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE schedule_jobs ADD COLUMN notify_room_id INT NULL"))
        except Exception:
            pass
