from datetime import datetime
from app.services.timezone_utils import utcnow
from sqlalchemy.orm import Session
from app.models.alert_case import AlertCase

def get_all(db: Session):
    return db.query(AlertCase).order_by(AlertCase.id.desc()).all()

def get_by_id(db: Session, item_id: int):
    return db.query(AlertCase).filter(AlertCase.id == item_id).first()

def get_by_case_key(db: Session, case_key: str):
    return db.query(AlertCase).filter(AlertCase.case_key == case_key).first()

def create_item(db: Session, **kwargs):
    row = AlertCase(**kwargs)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def update_item(db: Session, row: AlertCase, **kwargs):
    for key, value in kwargs.items():
        if hasattr(row, key):
            setattr(row, key, value)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row
