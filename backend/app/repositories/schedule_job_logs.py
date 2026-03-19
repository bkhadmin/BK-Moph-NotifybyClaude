from sqlalchemy.orm import Session
from app.models.schedule_job_log import ScheduleJobLog
from datetime import datetime

def create_item(db: Session, schedule_job_id:int, status:str, rows_returned:int|None=None, sent_count:int|None=None, error_message:str|None=None, detail_json:str|None=None):
    row = ScheduleJobLog(
        schedule_job_id=schedule_job_id,
        run_at=datetime.utcnow(),
        status=status,
        rows_returned=rows_returned,
        sent_count=sent_count,
        error_message=error_message,
        detail_json=detail_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_recent(db: Session, limit:int=100):
    return db.query(ScheduleJobLog).order_by(ScheduleJobLog.id.desc()).limit(limit).all()
