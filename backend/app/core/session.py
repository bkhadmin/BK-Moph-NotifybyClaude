import json,secrets,redis
from app.core.config import settings
def _client(): return redis.from_url(settings.redis_url, decode_responses=True)
def create_session(payload:dict)->str:
    sid=secrets.token_urlsafe(32); _client().setex(f'session:{sid}', settings.session_expire_hours*3600, json.dumps(payload, ensure_ascii=False)); return sid
def get_session(sid:str|None):
    if not sid: return None
    raw=_client().get(f'session:{sid}')
    return json.loads(raw) if raw else None
def destroy_session(sid:str|None):
    if sid: _client().delete(f'session:{sid}')
