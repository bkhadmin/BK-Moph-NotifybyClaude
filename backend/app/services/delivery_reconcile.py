from app.repositories.delivery_statuses import create_item as create_delivery_status
from app.repositories.send_logs import update_log_status

def ingest_status_callback(db, payload:dict):
    send_log_id = payload.get('send_log_id')
    external_message_id = payload.get('external_message_id') or payload.get('message_id')
    provider_status = payload.get('provider_status') or payload.get('status')
    normalized = 'delivered' if str(provider_status).lower() in ('delivered','success','sent') else 'failed'
    create_delivery_status(db, send_log_id, external_message_id, normalized, str(provider_status), str(payload))
    if send_log_id:
        update_log_status(db, int(send_log_id), normalized if normalized == 'delivered' else 'failed', detail=f"callback: {provider_status}")
    return {"ok": True, "normalized_status": normalized}
