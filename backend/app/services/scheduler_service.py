from datetime import datetime, timedelta

def _normalize_daily_time(value):
    raw = (value or "").strip()
    if "." in raw and ":" not in raw:
        raw = raw.replace(".", ":")
    if raw and ":" in raw:
        hh, mm = raw.split(":", 1)
        return f"{int(hh):02d}:{int(mm):02d}"
    return raw

def parse_next_run(schedule_type, cron_value=None, interval_minutes=None, base=None):
    base = base or datetime.now()
    st = (schedule_type or "").strip().lower()

    if st in ("once", "run_once"):
        if not cron_value:
            return base
        raw = str(cron_value).strip().replace("T", " ")
        return datetime.fromisoformat(raw)

    if st in ("interval", "every_minutes", "interval_minutes"):
        minutes = int(interval_minutes or cron_value or 5)
        return base + timedelta(minutes=minutes)

    if st in ("daily", "daily_time", "every_day_time"):
        raw = _normalize_daily_time(cron_value)
        if not raw or ":" not in raw:
            return base + timedelta(days=1)
        hh, mm = raw.split(":", 1)
        candidate = base.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        if candidate <= base:
            candidate = candidate + timedelta(days=1)
        return candidate

    if st in ("hourly",):
        return base.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    if st in ("monthly",):
        return base + timedelta(days=30)

    return base + timedelta(minutes=int(interval_minutes or 5))

def compute_following_next_run(job, base=None):
    return parse_next_run(
        getattr(job, "schedule_type", None),
        getattr(job, "cron_value", None),
        getattr(job, "interval_minutes", None),
        base=base or datetime.now(),
    )

def scheduler_now():
    return datetime.now()
