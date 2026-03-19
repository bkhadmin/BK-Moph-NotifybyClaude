import json
from sqlalchemy.orm import Session
from app.models.provider_profile_history import ProviderProfileHistory

def _normalize(value):
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {"raw": value}
    if isinstance(value, dict):
        return value
    return {"raw": str(value)}

def _diff(before, after):
    b = _normalize(before)
    a = _normalize(after)
    keys = sorted(set(b.keys()) | set(a.keys()))
    diff = {}
    for k in keys:
        if b.get(k) != a.get(k):
            diff[k] = {"before": b.get(k), "after": a.get(k)}
    return diff

def create_history(db:Session, provider_profile_id:int|None, action:str, changed_by:str|None, before_json, after_json):
    diff = _diff(before_json, after_json)
    row = ProviderProfileHistory(
        provider_profile_id=provider_profile_id,
        action=action,
        changed_by=changed_by,
        before_json=json.dumps(_normalize(before_json), ensure_ascii=False),
        after_json=json.dumps(_normalize(after_json), ensure_ascii=False),
        diff_json=json.dumps(diff, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get_all_for_profile(db:Session, provider_profile_id:int):
    return db.query(ProviderProfileHistory).filter(ProviderProfileHistory.provider_profile_id==provider_profile_id).order_by(ProviderProfileHistory.id.desc()).all()
