from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

from app.models.schedule_job_log import ScheduleJobLog

from app.models.alert_case import AlertCase
from app.models.alert_type_config import AlertTypeConfig

from app.models.notify_room import NotifyRoom
