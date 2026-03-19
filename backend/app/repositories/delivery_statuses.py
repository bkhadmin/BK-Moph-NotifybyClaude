from sqlalchemy.orm import Session
from app.models.delivery_status import DeliveryStatus

def create_item(db:Session, send_log_id:int|None, external_message_id:str|None, status:str, provider_status:str|None, detail:str|None=None):
    row=DeliveryStatus(send_log_id=send_log_id, external_message_id=external_message_id, status=status, provider_status=provider_status, detail=detail)
    db.add(row); db.commit(); db.refresh(row); return row

def get_all(db:Session):
    return db.query(DeliveryStatus).order_by(DeliveryStatus.id.desc()).all()
