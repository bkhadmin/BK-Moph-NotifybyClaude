from __future__ import annotations
from datetime import datetime, timedelta
import re
from croniter import croniter
from app.utils.thai_datetime import bangkok_now_naive

def _normalize_time_only(value:str) -> str:
    value = (value or "").strip().replace(".", ":")
    if re.fullmatch(r"\d{1,2}:\d{2}", value):
        return value
    raise ValueError("รูปแบบเวลาไม่ถูกต้อง ใช้เช่น 17:00 หรือ 17.00")

def _parse_once(value:str) -> datetime:
    value = (value or "").strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError("กำหนดการแบบครั้งเดียว ต้องใช้วันเวลาเต็ม เช่น 2026-03-17 17:00 หรือ 2026-03-17T17:00:00")

def _parse_daily(value:str, base:datetime) -> datetime:
    hhmm = _normalize_time_only(value)
    hh, mm = [int(x) for x in hhmm.split(":")]
    run_at = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if run_at <= base:
        run_at += timedelta(days=1)
    return run_at

def scheduler_now() -> datetime:
    return bangkok_now_naive()

def parse_next_run(schedule_type:str, cron_value:str|None, interval_minutes:int|None, base:datetime|None=None) -> datetime|None:
    base = base or scheduler_now()
    st = (schedule_type or "").strip().lower()

    if st == "once":
        if not cron_value:
            raise ValueError("กรุณาระบุวันเวลาแบบครั้งเดียว")
        return _parse_once(cron_value)

    if st == "daily":
        if not cron_value:
            raise ValueError("กรุณาระบุเวลา เช่น 17:00")
        return _parse_daily(cron_value, base)

    if st == "interval":
        if not interval_minutes or int(interval_minutes) <= 0:
            raise ValueError("interval_minutes ต้องมากกว่า 0")
        return base + timedelta(minutes=int(interval_minutes))

    if st == "cron":
        if not cron_value:
            raise ValueError("กรุณาระบุ cron expression")
        return croniter(cron_value, base).get_next(datetime)

    raise ValueError("schedule_type ไม่ถูกต้อง")

def compute_following_next_run(schedule_type:str, cron_value:str|None, interval_minutes:int|None, last_base:datetime|None=None):
    base = last_base or scheduler_now()
    st = (schedule_type or "").strip().lower()
    if st == "once":
        return None
    if st == "daily":
        return base + timedelta(days=1)
    if st == "interval":
        if not interval_minutes or int(interval_minutes) <= 0:
            return None
        return base + timedelta(minutes=int(interval_minutes))
    if st == "cron":
        if not cron_value:
            return None
        return croniter(cron_value, base).get_next(datetime)
    return None
