from sqlalchemy.orm import Session
from app.models.permission import Permission
def get_all(db:Session): return db.query(Permission).order_by(Permission.id.asc()).all()
