from sqlalchemy.orm import Session
from app.models.send_log import SendLog

def create_log(db:Session, actor:str|None, status:str, request_payload:str|None, response_payload:str|None, detail:str|None=None, retry_count:int=0):
    row=SendLog(actor=actor, status=status, request_payload=request_payload, response_payload=response_payload, detail=detail, retry_count=retry_count)
    db.add(row); db.commit(); db.refresh(row); return row

def update_log_status(db:Session, row_id:int, status:str, response_payload:str|None=None, detail:str|None=None, retry_count:int|None=None):
    row=db.query(SendLog).filter(SendLog.id==row_id).first()
    if not row: return None
    row.status=status
    if response_payload is not None: row.response_payload=response_payload
    if detail is not None: row.detail=detail
    if retry_count is not None: row.retry_count=retry_count
    db.commit(); db.refresh(row); return row

def get_all(db:Session): return db.query(SendLog).order_by(SendLog.id.desc()).all()
def get_failed_or_pending(db:Session):
    return db.query(SendLog).filter(SendLog.status.in_(['failed','retrying','pending'])).order_by(SendLog.id.asc()).all()
