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

_THAI_MONTHS_SHORT = [
    "", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
    "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]

def format_thai_datetime(dt, show_time=True):
    """Return Thai-locale datetime string with Buddhist Era year.
    e.g. '27 มี.ค. 2569 เวลา 14:30 น.'
    """
    local_dt = to_bangkok(dt)
    if not local_dt:
        return "-"
    d = local_dt.day
    m = _THAI_MONTHS_SHORT[local_dt.month]
    y = local_dt.year + 543
    if show_time:
        t = local_dt.strftime("%H:%M")
        return f"{d} {m} {y} เวลา {t} น."
    return f"{d} {m} {y}"

def format_thai_date(dt):
    return format_thai_datetime(dt, show_time=False)

def thai_date_str(value: str) -> str:
    """Convert a date string (DD/MM/YYYY or YYYY-MM-DD) to Thai Buddhist Era format.
    e.g. '18/03/2026' → '18 มี.ค. 2569'
         '2026-03-18' → '18 มี.ค. 2569'
    Returns original value if it cannot be parsed.
    """
    if not value:
        return value or "-"
    s = str(value).strip()
    from datetime import datetime as _dt
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            d = _dt.strptime(s, fmt)
            return f"{d.day} {_THAI_MONTHS_SHORT[d.month]} {d.year + 543}"
        except ValueError:
            continue
    return s
