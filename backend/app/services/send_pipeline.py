import json
from app.repositories.send_logs import create_log, update_log_status
from app.repositories.delivery_statuses import create_item as create_delivery_status
from app.repositories.notify_rooms import get_by_id as get_notify_room_by_id
from app.services.moph_notify import send_messages
from app.services.telegram_notify import send_telegram_messages
from app.services.flex_payload_sanitizer import sanitize_messages


def _get_channel_type(db, notify_room_id) -> str:
    """คืน channel_type ของ room หรือ 'moph_notify' ถ้าไม่พบ"""
    if db is not None and notify_room_id:
        try:
            room = get_notify_room_by_id(db, int(notify_room_id))
            if room:
                return getattr(room, "channel_type", None) or "moph_notify"
        except Exception:
            pass
    return "moph_notify"


async def _dispatch(messages, db, notify_room_id, retries):
    """ส่งข้อความตาม channel_type ของ room"""
    channel = _get_channel_type(db, notify_room_id)
    if channel == "telegram":
        room = get_notify_room_by_id(db, int(notify_room_id))
        bot_token = (room.client_key or "").strip()
        chat_id = (room.secret_key or "").strip()
        result = await send_telegram_messages(messages, bot_token=bot_token, chat_id=chat_id, retries=retries)
        result["room_name"] = getattr(room, "name", None)
        result["room_id"] = getattr(room, "id", None)
        return result
    return await send_messages(messages, db=db, notify_room_id=notify_room_id, retries=retries)


async def send_with_log(db, username, messages, detail, notify_room_id=None):
    actor = username or "system"
    messages = sanitize_messages(messages)
    log = create_log(db, actor, "pending", json.dumps(messages, ensure_ascii=False), None, detail, retry_count=0)
    try:
        result = await _dispatch(messages, db=db, notify_room_id=notify_room_id, retries=3)
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
