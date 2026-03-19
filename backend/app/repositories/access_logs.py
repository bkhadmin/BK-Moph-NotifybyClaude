from sqlalchemy.orm import Session
from app.models.access_log import AccessLog
def write_log(db:Session, actor:str|None, ip_address:str|None, action:str, status:str, detail:str|None=None):
    row=AccessLog(actor=actor, ip_address=ip_address, action=action, status=status, detail=detail); db.add(row); db.commit(); db.refresh(row); return row
def get_all(db:Session): return db.query(AccessLog).order_by(AccessLog.id.desc()).all()
