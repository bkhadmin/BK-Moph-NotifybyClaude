import json
from app.repositories.send_logs import create_log, update_log_status
from app.repositories.delivery_statuses import create_item as create_delivery_status
from app.services.moph_notify import send_messages
from app.services.flex_payload_sanitizer import sanitize_messages

async def send_with_log(db, username, messages, detail, notify_room_id=None):
    actor = username or "system"
    messages = sanitize_messages(messages)
    log = create_log(db, actor, "pending", json.dumps(messages, ensure_ascii=False), None, detail, retry_count=0)
    try:
        result = await send_messages(messages, db=db, notify_room_id=notify_room_id, retries=3)
        update_log_status(db, log.id, "success", json.dumps(result, ensure_ascii=False), detail, retry_count=max(0, int(result.get("attempt", 1)) - 1))
        create_delivery_status(db, log.id, None, "accepted", str(result.get("data")), detail)
        return result, log.id
    except Exception as exc:
        update_log_status(db, log.id, "failed", None, f"{detail} | {exc}", retry_count=3)
        create_delivery_status(db, log.id, None, "failed", None, str(exc))
        raise

async def retry_failed_log(db, send_log_row):
    payload = sanitize_messages(json.loads(send_log_row.request_payload or "[]"))
    try:
        result = await send_messages(payload, db=db, retries=2)
        update_log_status(db, send_log_row.id, "success", json.dumps(result, ensure_ascii=False), send_log_row.detail, retry_count=send_log_row.retry_count + max(0, int(result.get("attempt", 1)) - 1))
        create_delivery_status(db, send_log_row.id, None, "accepted", str(result.get("data")), "retry success")
        return True
    except Exception as exc:
        update_log_status(db, send_log_row.id, "retrying" if send_log_row.retry_count < 5 else "failed", None, f"{send_log_row.detail} | retry error: {exc}", retry_count=send_log_row.retry_count + 1)
        create_delivery_status(db, send_log_row.id, None, "failed", None, f"retry error: {exc}")
        return False
