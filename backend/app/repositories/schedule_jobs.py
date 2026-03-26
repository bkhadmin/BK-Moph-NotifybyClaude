from sqlalchemy.orm import Session
from app.models.schedule_job import ScheduleJob

def get_all(db: Session):
    return db.query(ScheduleJob).order_by(ScheduleJob.id.desc()).all()

def get_due_jobs(db: Session, now):
    return db.query(ScheduleJob).filter(ScheduleJob.is_active == 'Y', ScheduleJob.next_run_at != None, ScheduleJob.next_run_at <= now).order_by(ScheduleJob.next_run_at.asc()).all()

def get_by_id(db: Session, item_id: int):
    return db.query(ScheduleJob).filter(ScheduleJob.id == item_id).first()

def create_item(db: Session, name: str, schedule_type: str, cron_value=None, interval_minutes=None, approved_query_id=None, message_template_id=None, notify_room_id=None, next_run_at=None, is_active='Y', payload=None, payload_json=None):
    row = ScheduleJob(name=name, schedule_type=schedule_type, cron_value=cron_value, interval_minutes=interval_minutes, approved_query_id=approved_query_id, message_template_id=message_template_id, notify_room_id=notify_room_id, next_run_at=next_run_at, is_active=is_active, payload_json=payload_json if payload_json is not None else payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def update_item(db: Session, row: ScheduleJob, **kwargs):
    for key, value in kwargs.items():
        if hasattr(row, key):
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row

def delete_item(db: Session, row: ScheduleJob):
    db.delete(row)
    db.commit()
