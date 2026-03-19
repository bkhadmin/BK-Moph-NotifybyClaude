from datetime import datetime, timedelta, timezone

THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
]

BANGKOK_TZ = timezone(timedelta(hours=7))

def bangkok_now() -> datetime:
    return datetime.now(BANGKOK_TZ)

def bangkok_now_naive() -> datetime:
    return bangkok_now().replace(tzinfo=None)

def to_bangkok_naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(BANGKOK_TZ).replace(tzinfo=None)

def format_thai_date(dt: datetime) -> str:
    if not dt:
        return ""
    day = dt.day
    month = THAI_MONTHS[dt.month]
    year = dt.year + 543
    return f"{day} {month} {year}"

def format_thai_time(dt: datetime) -> str:
    if not dt:
        return ""
    return dt.strftime("%H.%M") + " น."

def format_thai_datetime(dt: datetime) -> str:
    if not dt:
        return ""
    local_dt = to_bangkok_naive(dt) or dt
    return f"{format_thai_date(local_dt)} เวลา {local_dt.strftime('%H.%M')} น."
