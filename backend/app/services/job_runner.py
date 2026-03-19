from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories.approved_queries import get_by_id as get_query_by_id
from app.repositories.message_templates import get_by_id as get_template_by_id
from app.services.hosxp_query import preview_query
from app.services.template_render import build_message_payload
from app.services.scheduler_service import next_after_run
from app.services.send_pipeline import send_with_log

async def run_job(db:Session, job):
    q = get_query_by_id(db, job.approved_query_id) if job.approved_query_id else None
    t = get_template_by_id(db, job.message_template_id) if job.message_template_id else None
    if not q or not t:
        return None
    data = preview_query(q.sql_text, max_rows=q.max_rows)
    messages = [build_message_payload(t.template_type, t.content, t.alt_text, row) for row in data['rows']]
    await send_with_log(db, 'scheduler', messages, f'job_id={job.id}')
    last_run = datetime.now()
    next_run = next_after_run(job.schedule_type, job.cron_value, job.interval_minutes, last_run)
    return {"next_run_at": next_run, "last_run_at": last_run}
