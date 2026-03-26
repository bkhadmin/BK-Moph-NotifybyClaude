import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")

def utcnow():
    return datetime.now(timezone.utc)

def bangkok_now():
    return datetime.now(BANGKOK_TZ)

def _legacy_mode():
    return (os.getenv("LEGACY_DB_TIME_MODE") or "utc").strip().lower()

def to_bangkok(dt):
    if not dt:
        return None
    if getattr(dt, "tzinfo", None) is None:
        mode = _legacy_mode()
        if mode == "bangkok":
            dt = dt.replace(tzinfo=BANGKOK_TZ)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BANGKOK_TZ)

def format_bangkok(dt, fmt="%d/%m/%Y %H:%M:%S"):
    local_dt = to_bangkok(dt)
    if not local_dt:
        return ""
    return local_dt.strftime(fmt)

def today_bangkok_str(fmt="%d/%m/%Y"):
    return datetime.now(BANGKOK_TZ).strftime(fmt)
