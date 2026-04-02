import json
import os
from sqlalchemy.orm import Session
from app.services.timezone_write import bangkok_now_naive
from app.repositories.approved_queries import get_by_id as get_query_by_id
from app.repositories.message_templates import get_by_id as get_template_by_id
from app.services.hosxp_query import preview_query
from app.services.template_render import build_message_payload
from app.services.scheduler_service import next_after_run
from app.services.send_pipeline import send_with_log
from app.services.dynamic_template_renderer import build_dynamic_template_payload
from app.services.flex_template_merger import build_flex_payload_from_template_rows
from app.services.alert_case_service import enrich_alert_rows, normalize_alert_row_identity, mark_rows_sent
from app.services.flex_payload_sanitizer import sanitize_messages

# Template types that need the full claim/alert pipeline
_CLAIM_TYPES = {"lab_critical_claim", "claim_alert"}
# Template types that produce one message per dataset (not per row)
_DYNAMIC_TYPES = {"flex_full_list", "dynamic_full_list", "flex_top5", "flex_carousel",
                  "flex_dynamic", "lab_critical_claim", "claim_alert"}


def _resolve_alert_cfg(db, template_type: str, content: str):
    """Return alert config dict from DB if available, else None."""
    try:
        tc = json.loads(content or "{}")
        alert_type_code = tc.get("alert_type_code")
        if not alert_type_code and template_type == "lab_critical_claim":
            alert_type_code = "lab_critical"
        if alert_type_code:
            from app.repositories.alert_type_configs import get_by_code, to_cfg_dict
            cfg_row = get_by_code(db, alert_type_code)
            if cfg_row:
                return to_cfg_dict(cfg_row)
    except Exception:
        pass
    return None


async def run_job(db: Session, job):
    q = get_query_by_id(db, job.approved_query_id) if job.approved_query_id else None
    t = get_template_by_id(db, job.message_template_id) if job.message_template_id else None
    if not q or not t:
        return None

    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = data.get("rows") or []

    template_type = (t.template_type or "").strip().lower()

    # Resolve alert cfg for claim types
    alert_cfg = _resolve_alert_cfg(db, template_type, t.content) if template_type in _CLAIM_TYPES else None

    # Enrich and filter rows for claim types
    if template_type in _CLAIM_TYPES:
        try:
            base_url = os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or ""
            rows = enrich_alert_rows(db, rows, base_url, alert_cfg=alert_cfg, notify_room_id=getattr(job, "notify_room_id", None))
            rows = [normalize_alert_row_identity(r) for r in (rows or [])]
        except Exception:
            pass
        filtered = []
        for row in rows:
            item = dict(row)
            if str(item.get("case_status") or "").upper().strip() == "CLAIMED" or str(item.get("claimed_by") or "").strip():
                continue
            item["case_status_text"] = "รอรับเคส"
            filtered.append(item)
        if not filtered:
            return None
        rows = filtered

    # Build messages
    dynamic_payload = build_dynamic_template_payload(template_type, t.content, t.alt_text, rows, alert_cfg=alert_cfg)
    if dynamic_payload is not None:
        messages = dynamic_payload
    elif template_type == "flex":
        messages = build_flex_payload_from_template_rows(t.content, t.alt_text, rows)
    else:
        messages = [build_message_payload(t.template_type, t.content, t.alt_text, row) for row in rows[:10]]

    messages = sanitize_messages(messages)
    if not messages:
        return None

    notify_room_id = getattr(job, 'notify_room_id', None)
    await send_with_log(db, 'scheduler', messages, f'job_id={job.id}', notify_room_id=notify_room_id)

    if template_type in _CLAIM_TYPES:
        try:
            mark_rows_sent(db, rows)
        except Exception:
            pass

    last_run = bangkok_now_naive()
    next_run = next_after_run(job.schedule_type, job.cron_value, job.interval_minutes, last_run)
    return {"next_run_at": next_run, "last_run_at": last_run}
