from sqlalchemy.orm import Session
from app.models.role import Role
def get_by_code(db:Session, code:str): return db.query(Role).filter(Role.code==code).first()
def get_all(db:Session): return db.query(Role).order_by(Role.id.asc()).all()
