from sqlalchemy.orm import Session
from app.models.ip_ban import IpBan
def get_by_ip(db:Session, ip:str): return db.query(IpBan).filter(IpBan.ip_address==ip).first()
def touch_fail(db:Session, ip:str, threshold:int):
    row=get_by_ip(db, ip)
    if not row:
        row=IpBan(ip_address=ip, fail_count=0, is_banned='N'); db.add(row); db.flush()
    row.fail_count += 1
    if row.fail_count >= threshold: row.is_banned='Y'
    db.commit(); db.refresh(row); return row
def clear_fail(db:Session, ip:str):
    row=get_by_ip(db, ip)
    if row:
        row.fail_count=0; row.is_banned='N'; db.commit()
    return row
