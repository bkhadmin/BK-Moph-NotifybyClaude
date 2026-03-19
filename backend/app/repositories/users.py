import json
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.provider_profiles import upsert_profile

def get_by_username(db:Session, username:str):
    return db.query(User).filter(User.username==username).first()

def get_by_id(db:Session, user_id:int):
    return db.query(User).filter(User.id==user_id).first()

def get_all(db:Session):
    return db.query(User).order_by(User.id.desc()).all()

def update_role(db:Session, user:User, role_id:int|None):
    user.role_id = role_id
    db.commit()
    db.refresh(user)
    return user

def normalize_username(profile:dict)->str:
    return (
        profile.get('username')
        or profile.get('provider_id')
        or profile.get('account_id')
        or profile.get('hash_cid')
        or 'provider-user'
    )

def normalize_display_name(profile:dict)->str:
    return (
        profile.get('name_th')
        or profile.get('display_name')
        or profile.get('name')
        or 'Provider User'
    )

def upsert_provider_user(db:Session, profile:dict, default_role_id:int|None=None):
    account_id=profile.get('account_id')
    provider_id=profile.get('provider_id')
    username=normalize_username(profile)

    user=None
    if account_id:
        user=db.query(User).filter(User.provider_account_id==account_id).first()
    if not user and provider_id:
        user=db.query(User).filter(User.provider_id==provider_id).first()
    if not user:
        user=db.query(User).filter(User.username==username).first()

    if not user:
        user=User(username=username, auth_type='provider', role_id=default_role_id)
        db.add(user)

    user.display_name=normalize_display_name(profile)
    user.provider_account_id=account_id
    user.provider_id=provider_id
    user.profile_json=json.dumps(profile, ensure_ascii=False)
    db.commit()
    db.refresh(user)

    upsert_profile(db, user.id, profile, changed_by='provider_login')
    return user
