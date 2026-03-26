from sqlalchemy.orm import Session
from app.models.permission import Permission
def get_all(db:Session): return db.query(Permission).order_by(Permission.id.asc()).all()


def ensure_module53_permissions(db):
    needed = [
        ("notify_rooms", "Notify Rooms"),
        ("claim_notify_settings", "Claim Notify Settings"),
    ]
    try:
        from app.models.permission import Permission
        for code, name in needed:
            row = db.query(Permission).filter(Permission.code == code).first()
            if not row:
                db.add(Permission(code=code, name=name))
        db.commit()
    except Exception:
        db.rollback()
