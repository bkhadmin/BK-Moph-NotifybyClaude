from sqlalchemy.orm import Session
from app.models.media_file import MediaFile
def create_item(db:Session, original_name:str, stored_name:str, mime_type:str|None, width:int|None, height:int|None, public_url:str):
    row=MediaFile(original_name=original_name, stored_name=stored_name, mime_type=mime_type, width=width, height=height, public_url=public_url)
    db.add(row); db.commit(); db.refresh(row); return row
def get_all(db:Session): return db.query(MediaFile).order_by(MediaFile.id.desc()).all()
def get_by_id(db:Session, item_id:int): return db.query(MediaFile).filter(MediaFile.id==item_id).first()
