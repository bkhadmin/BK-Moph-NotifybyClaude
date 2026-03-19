import json
from sqlalchemy.orm import Session
from app.models.provider_profile import ProviderProfile
from app.repositories.provider_profile_histories import create_history

def _pick(profile:dict, *keys):
    for k in keys:
        value = profile.get(k)
        if value not in (None, ''):
            return value
    return None

def _nested(profile:dict, parent:str, child:str):
    block = profile.get(parent)
    if isinstance(block, dict):
        return block.get(child)
    return None

def _row_to_dict(row:ProviderProfile):
    return {
        "user_id": row.user_id,
        "account_id": row.account_id,
        "provider_id": row.provider_id,
        "hash_cid": row.hash_cid,
        "title_name": row.title_name,
        "name_th": row.name_th,
        "first_name": row.first_name,
        "last_name": row.last_name,
        "position_name": row.position_name,
        "organization_name": row.organization_name,
        "organization_code": row.organization_code,
        "license_no": row.license_no,
        "phone": row.phone,
        "email": row.email,
    }

def upsert_profile(db:Session, user_id:int|None, profile:dict, changed_by:str|None='provider_login'):
    account_id = profile.get('account_id')
    provider_id = profile.get('provider_id')
    row = None
    if account_id:
        row = db.query(ProviderProfile).filter(ProviderProfile.account_id == account_id).first()
    if not row and provider_id:
        row = db.query(ProviderProfile).filter(ProviderProfile.provider_id == provider_id).first()
    if not row and user_id:
        row = db.query(ProviderProfile).filter(ProviderProfile.user_id == user_id).first()

    before_json = None
    action = 'create'
    if not row:
        row = ProviderProfile()
        db.add(row)
    else:
        before_json = _row_to_dict(row)
        action = 'update'

    row.user_id = user_id
    row.account_id = account_id
    row.provider_id = provider_id
    row.hash_cid = _pick(profile, 'hash_cid', 'cid_hash')
    row.title_name = _pick(profile, 'title_name', 'title', 'prefix')
    row.name_th = _pick(profile, 'name_th', 'display_name', 'name')
    row.first_name = _pick(profile, 'first_name', 'fname', 'first_name_th')
    row.last_name = _pick(profile, 'last_name', 'lname', 'last_name_th')
    row.position_name = _pick(profile, 'position_name', 'position')
    row.organization_name = _pick(profile, 'organization_name') or _nested(profile, 'organization', 'name')
    row.organization_code = _pick(profile, 'organization_code', 'hcode') or _nested(profile, 'organization', 'code')
    row.license_no = _pick(profile, 'license_no', 'license', 'medical_license')
    row.phone = _pick(profile, 'phone', 'mobile', 'tel')
    row.email = _pick(profile, 'email')
    row.raw_json = json.dumps(profile, ensure_ascii=False)
    db.commit()
    db.refresh(row)

    after_json = _row_to_dict(row)
    create_history(db, row.id, action, changed_by, before_json, after_json)
    return row

def update_profile_manual(db:Session, row:ProviderProfile, payload:dict, changed_by:str|None):
    before_json = _row_to_dict(row)
    row.name_th = payload.get('name_th')
    row.position_name = payload.get('position_name')
    row.organization_name = payload.get('organization_name')
    row.organization_code = payload.get('organization_code')
    row.license_no = payload.get('license_no')
    row.phone = payload.get('phone')
    row.email = payload.get('email')
    db.commit()
    db.refresh(row)
    after_json = _row_to_dict(row)
    create_history(db, row.id, 'manual_update', changed_by, before_json, after_json)
    return row

def get_all(db:Session):
    return db.query(ProviderProfile).order_by(ProviderProfile.id.desc()).all()

def get_by_id(db:Session, item_id:int):
    return db.query(ProviderProfile).filter(ProviderProfile.id == item_id).first()
