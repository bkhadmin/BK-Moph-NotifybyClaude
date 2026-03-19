from sqlalchemy.orm import Session
from app.models.message_template import MessageTemplate

def get_all(db:Session):
    return db.query(MessageTemplate).order_by(MessageTemplate.id.desc()).all()

def get_by_id(db:Session, item_id:int):
    return db.query(MessageTemplate).filter(MessageTemplate.id==item_id).first()

def create_item(db:Session, name:str, template_type:str, content:str, alt_text:str|None=None):
    row=MessageTemplate(name=name, template_type=template_type, content=content, alt_text=alt_text, is_active=True)
    db.add(row); db.commit(); db.refresh(row); return row

def update_item(db:Session, row:MessageTemplate, name:str, template_type:str, content:str, alt_text:str|None=None):
    row.name = name
    row.template_type = template_type
    row.content = content
    row.alt_text = alt_text
    db.commit(); db.refresh(row); return row

def delete_item(db:Session, row:MessageTemplate):
    db.delete(row)
    db.commit()

def clone_item(db:Session, row:MessageTemplate, new_name:str|None=None):
    cloned = MessageTemplate(
        name=new_name or f"{row.name} (Copy)",
        template_type=row.template_type,
        content=row.content,
        alt_text=row.alt_text,
        is_active=True,
    )
    db.add(cloned)
    db.commit()
    db.refresh(cloned)
    return cloned
