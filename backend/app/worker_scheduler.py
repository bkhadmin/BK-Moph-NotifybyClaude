import os
import asyncio
import json
import time
from datetime import timedelta

from sqlalchemy import text
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.repositories.schedule_jobs import get_due_jobs, get_by_id, update_item
from app.repositories.schedule_job_logs import create_item as create_job_log
from app.repositories.message_templates import get_by_id as get_template
from app.repositories.approved_queries import get_by_id as get_query
from app.services.hosxp_query import preview_query
from app.services.flex_template_merger import build_flex_payload_from_template_rows
from app.services.dynamic_template_renderer import build_dynamic_template_payload
from app.services.scheduler_service import compute_following_next_run, scheduler_now
from app.services.template_render import build_message_payload
from app.services.send_pipeline import send_with_log
from app.services.alert_case_service import enrich_alert_rows, mark_alert_case_sent, normalize_alert_row_identity
from app.services.flex_payload_sanitizer import sanitize_messages

POLL_SECONDS = 5

def ensure_tables():
    Base.metadata.create_all(bind=engine)

def _job_config(job):
    try:
        return json.loads(job.payload_json or "{}")
    except Exception:
        return {}

def _build_messages(db, job):
    q = get_query(db, job.approved_query_id) if job.approved_query_id else None
    t = get_template(db, job.message_template_id) if job.message_template_id else None
    if not q or not t:
        raise ValueError("approved query หรือ message template ไม่พบ")

    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = data.get("rows") or []

    # Resolve alert type config from template content
    alert_cfg = None
    try:
        tc = json.loads(t.content or "{}")
        alert_type_code = tc.get("alert_type_code")
        if not alert_type_code and t.template_type == "lab_critical_claim":
            alert_type_code = "lab_critical"
        if alert_type_code:
            from app.repositories.alert_type_configs import get_by_code as _get_atc, to_cfg_dict as _atc_dict
            cfg_row = _get_atc(db, alert_type_code)
            if cfg_row:
                alert_cfg = _atc_dict(cfg_row)
    except Exception:
        pass

    # enrich alert rows with case_key / claim_url / claim status, then skip already-claimed cases
    try:
        base_url = os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "http://192.168.191.12:8012"
        enriched_rows = enrich_alert_rows(db, rows, base_url, alert_cfg=alert_cfg, notify_room_id=getattr(job, "notify_room_id", None))
        enriched_rows = [normalize_alert_row_identity(x) for x in (enriched_rows or [])]
    except Exception:
        enriched_rows = rows

    filtered_rows = []
    for row in enriched_rows or []:
        item = dict(row)
        status = str(item.get("case_status") or "").upper().strip()
        claimed_by = str(item.get("claimed_by") or "").strip()
        if status == "CLAIMED" or claimed_by:
            continue
        item["case_status_text"] = "รอรับเคส"
        filtered_rows.append(item)

    if not filtered_rows:
        return [], []

    dynamic_payload = build_dynamic_template_payload(t.template_type, t.content, t.alt_text, filtered_rows, alert_cfg=alert_cfg)
    if dynamic_payload is not None:
        messages = dynamic_payload
    elif t.template_type == "flex":
        messages = build_flex_payload_from_template_rows(t.content, t.alt_text, filtered_rows)
    else:
        messages = [build_message_payload(t.template_type, t.content, t.alt_text, row) for row in filtered_rows[:10]]

    messages = sanitize_messages(messages)
    return filtered_rows, messages

def _safe_create_log(db, **kwargs):
    try:
        create_job_log(db, **kwargs)
    except Exception as e:
        print(f"[scheduler] _safe_create_log ERROR: {e} kwargs={list(kwargs.keys())}")
        db.rollback()

def _detail(job):
    return f"schedule_job_id={job.id}, approved_query_id={job.approved_query_id}, template_id={job.message_template_id}, notify_room_id={getattr(job, 'notify_room_id', None)}"

def _finalize_success(db, job, now, rows, messages, result):
    print(f"[scheduler] _finalize_success called job_id={job.id}")
    _safe_create_log(
        db,
        schedule_job_id=job.id,
        run_at=now,
        status="success",
        rows_returned=len(rows),
        sent_count=len(messages),
        detail_json=json.dumps(result, ensure_ascii=False),
    )
    cfg = _job_config(job)
    cfg["retry_count"] = 0
    next_run = compute_following_next_run(job, base=now)
    update_item(
        db,
        job,
        last_run_at=now,
        next_run_at=next_run,
        is_active="N" if job.schedule_type == "once" else job.is_active,
        payload_json=json.dumps(cfg, ensure_ascii=False),
    )
    print(f"[scheduler] success job_id={job.id} rows={len(rows)} sent={len(messages)} next_run_at={next_run} room_id={getattr(job, 'notify_room_id', None)}")

def _finalize_failure(db, job, now, rows, messages, exc):
    db.rollback()
    cfg = _job_config(job)
    retry_limit = int(cfg.get("retry_limit", 3))
    retry_count = int(cfg.get("retry_count", 0)) + 1
    cfg["retry_count"] = retry_count
    _safe_create_log(
        db,
        schedule_job_id=job.id,
        run_at=now,
        status="failed",
        rows_returned=len(rows) if rows else 0,
        sent_count=len(messages) if messages else 0,
        error_message=str(exc),
        detail_json=json.dumps(cfg, ensure_ascii=False),
    )
    if retry_count < retry_limit:
        next_run = now + timedelta(minutes=5)
        update_item(db, job, last_run_at=now, next_run_at=next_run, payload_json=json.dumps(cfg, ensure_ascii=False))
    else:
        cfg["retry_count"] = 0
        next_run = compute_following_next_run(job, base=now) if job.schedule_type != "once" else None
        update_item(
            db,
            job,
            last_run_at=now,
            next_run_at=next_run,
            is_active="N" if job.schedule_type == "once" else job.is_active,
            payload_json=json.dumps(cfg, ensure_ascii=False),
        )
    print(f"[scheduler] failed job_id={job.id} error={exc} next_run_at={next_run} retry_count={cfg.get('retry_count')} room_id={getattr(job, 'notify_room_id', None)}")

def execute_job(db, job):
    now = scheduler_now()
    rows = []
    messages = []
    try:
        rows, messages = _build_messages(db, job)

        if not rows or not messages:
            _safe_create_log(
                db,
                schedule_job_id=job.id,
                run_at=now,
                status="no_data",
                rows_returned=len(rows) if rows else 0,
                sent_count=0,
                detail_json=json.dumps({
                    "message": "no rows returned; skip send",
                    "notify_room_id": getattr(job, "notify_room_id", None),
                }, ensure_ascii=False),
            )
            cfg = _job_config(job)
            cfg["retry_count"] = 0
            next_run = compute_following_next_run(job, base=now)
            update_item(
                db,
                job,
                last_run_at=now,
                next_run_at=next_run,
                is_active="N" if job.schedule_type == "once" else job.is_active,
                payload_json=json.dumps(cfg, ensure_ascii=False),
            )
            print(f"[scheduler] no_data job_id={job.id} next_run_at={next_run} room_id={getattr(job, 'notify_room_id', None)}")
            return {"status": "no_data", "rows": len(rows) if rows else 0, "sent": 0}

        use_alertroom = getattr(job, 'use_alertroom', 'N') == 'Y'
        if use_alertroom:
            # รวม alertroom codes จากทุก row แล้วส่งไปแต่ละห้อง
            codes = set()
            for row in rows:
                av = str(row.get('alertroom') or '').strip()
                for c in av.split(','):
                    if c.strip():
                        codes.add(c.strip())
            from app.repositories.notify_rooms import get_by_room_codes
            target_rooms = get_by_room_codes(db, list(codes))
            room_code_to_id = {r.room_code: r.id for r in target_rooms}
            send_log_id = None
            result = {}
            for room in target_rooms:
                r, lid = asyncio.run(send_with_log(
                    db, "scheduler", messages,
                    f"schedule_job_id={job.id}, approved_query_id={job.approved_query_id}, template_id={job.message_template_id}, alertroom={room.room_code}",
                    notify_room_id=room.id,
                ))
                result = dict(r or {})
                send_log_id = lid
            result["send_log_id"] = send_log_id
            updated_cases = 0
            for row in rows or []:
                try:
                    case_key = row.get("case_key") if isinstance(row, dict) else getattr(row, "case_key", None)
                    lab_order_number = row.get("lab_order_number") if isinstance(row, dict) else getattr(row, "lab_order_number", None)
                    if mark_alert_case_sent(db, case_key=case_key, lab_order_number=lab_order_number):
                        updated_cases += 1
                    row_code = str(row.get('alertroom') or '').strip().split(',')[0].strip()
                    row_room_id = room_code_to_id.get(row_code)
                    if row_room_id and case_key:
                        db.execute(
                            text("UPDATE alert_cases SET notify_room_id=:rid WHERE case_key=:ck AND notify_room_id IS NULL"),
                            {"rid": row_room_id, "ck": case_key}
                        )
                except Exception:
                    pass
        else:
            result, send_log_id = asyncio.run(
                send_with_log(
                    db,
                    "scheduler",
                    messages,
                    _detail(job),
                    notify_room_id=getattr(job, "notify_room_id", None),
                )
            )
            result = dict(result or {})
            result["send_log_id"] = send_log_id
            updated_cases = 0
            job_notify_room_id = getattr(job, "notify_room_id", None)
            for row in rows or []:
                try:
                    case_key = row.get("case_key") if isinstance(row, dict) else getattr(row, "case_key", None)
                    lab_order_number = row.get("lab_order_number") if isinstance(row, dict) else getattr(row, "lab_order_number", None)
                    if mark_alert_case_sent(db, case_key=case_key, lab_order_number=lab_order_number):
                        updated_cases += 1
                    if job_notify_room_id and case_key:
                        db.execute(
                            text("UPDATE alert_cases SET notify_room_id=:rid WHERE case_key=:ck AND notify_room_id IS NULL"),
                            {"rid": job_notify_room_id, "ck": case_key}
                        )
                except Exception:
                    pass
        db.commit()
        db.expire_all()
        result["updated_cases"] = updated_cases

        _finalize_success(db, job, now, rows, messages, result)
        return {"status": "success", "rows": len(rows), "sent": len(messages), "send_log_id": send_log_id, "updated_cases": updated_cases}
    except Exception as exc:
        _finalize_failure(db, job, now, rows, messages, exc)
        return {"status": "failed", "error": str(exc), "rows": len(rows), "sent": len(messages)}

def run_job_now(job_id: int):
    ensure_tables()
    db = SessionLocal()
    try:
        job = get_by_id(db, job_id)
        if not job:
            return {"status": "not_found"}
        return execute_job(db, job)
    finally:
        db.close()

def run_once():
    ensure_tables()
    db = SessionLocal()
    try:
        now = scheduler_now()
        jobs = get_due_jobs(db, now)
        print(f"[scheduler] now={now} due_jobs={[j.id for j in jobs]}")
        for job in jobs:
            execute_job(db, job)
    finally:
        db.close()

def main():
    ensure_tables()
    print("[scheduler] worker started")
    while True:
        run_once()
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    main()
