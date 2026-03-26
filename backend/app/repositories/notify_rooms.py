from sqlalchemy.orm import Session
from app.models.notify_room import NotifyRoom

def get_all(db: Session):
    return db.query(NotifyRoom).order_by(NotifyRoom.name.asc()).all()

def get_active(db: Session):
    return db.query(NotifyRoom).filter(NotifyRoom.is_active == "Y").order_by(NotifyRoom.name.asc()).all()

def get_by_id(db: Session, room_id: int):
    return db.query(NotifyRoom).filter(NotifyRoom.id == room_id).first()

def create_item(db: Session, name: str, room_code: str | None, client_key: str, secret_key: str, is_active: str="Y", note: str | None=None):
    row = NotifyRoom(name=name.strip(), room_code=(room_code or '').strip() or None, client_key=client_key.strip(), secret_key=secret_key.strip(), is_active=is_active or 'Y', note=(note or '').strip() or None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def update_item(db: Session, row: NotifyRoom, **kwargs):
    for k, v in kwargs.items():
        if hasattr(row, k):
            setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

def delete_item(db: Session, row: NotifyRoom):
    db.delete(row)
    db.commit()
