from sqlalchemy.orm import Session
from app.models.approved_query import ApprovedQuery

def get_all(db:Session):
    return db.query(ApprovedQuery).order_by(ApprovedQuery.id.desc()).all()

def get_by_id(db:Session, item_id:int):
    return db.query(ApprovedQuery).filter(ApprovedQuery.id==item_id).first()

def create_item(db:Session, name:str, sql_text:str, max_rows:int):
    row=ApprovedQuery(name=name, sql_text=sql_text, max_rows=max_rows, is_active=True)
    db.add(row); db.commit(); db.refresh(row); return row

def update_item(db:Session, row:ApprovedQuery, name:str, sql_text:str, max_rows:int):
    row.name = name
    row.sql_text = sql_text
    row.max_rows = max_rows
    db.commit(); db.refresh(row); return row

def delete_item(db:Session, row:ApprovedQuery):
    db.delete(row)
    db.commit()
