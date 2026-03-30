from sqlalchemy.orm import Session
from app.models.access_log import AccessLog
from app.services.timezone_write import bangkok_now_naive

def write_log(db:Session, actor:str|None, ip_address:str|None, action:str, status:str, detail:str|None=None):
    row=AccessLog(actor=actor, ip_address=ip_address, action=action, status=status, detail=detail, created_at=bangkok_now_naive())
    db.add(row); db.commit(); db.refresh(row); return row

def get_all(db:Session): return db.query(AccessLog).order_by(AccessLog.id.desc()).all()

def get_filtered(db:Session, date_from:str|None=None, date_to:str|None=None):
    q = db.query(AccessLog)
    if date_from:
        q = q.filter(AccessLog.created_at >= date_from + ' 00:00:00')
    if date_to:
        q = q.filter(AccessLog.created_at <= date_to + ' 23:59:59')
    return q.order_by(AccessLog.id.desc()).all()
