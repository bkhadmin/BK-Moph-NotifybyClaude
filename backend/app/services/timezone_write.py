from datetime import datetime
from zoneinfo import ZoneInfo

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")

def bangkok_now_naive():
    return datetime.now(BANGKOK_TZ).replace(tzinfo=None)

def bangkok_now_str():
    return bangkok_now_naive().strftime("%Y-%m-%d %H:%M:%S")
