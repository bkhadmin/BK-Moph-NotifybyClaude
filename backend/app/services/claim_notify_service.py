import re
import asyncio
from app.services.timezone_utils import format_thai_datetime
from app.services.send_pipeline import send_with_log

_FIELD_RE = re.compile(r"\{([a-zA-Z0-9_ก-๙]+)\}")

_DEFAULT_TEMPLATE = (
    "✅ รับเคสเรียบร้อย\n\n"
    "ผู้ป่วย: {patient_name}\n"
    "HN: {patient_hn}\n"
    "รายการ: {item_name}\n"
    "ค่า: {item_value}\n"
    "แผนก: {department}\n"
    "ผู้รับเคส: {claimed_by}\n"
    "เวลารับเคส: {claimed_at}\n"
    "สถานะ: รับเคสแล้ว"
)


def _render_template(template: str, variables: dict) -> str:
    return _FIELD_RE.sub(lambda m: str(variables.get(m.group(1), "-")), template)


def build_claim_notification_text(case, claim_notify_template: str = "") -> str:
    template = claim_notify_template.strip() if claim_notify_template else _DEFAULT_TEMPLATE
    variables = {
        "patient_name": case.patient_name or "-",
        "patient_hn":   case.patient_hn or "-",
        "item_name":    case.item_name or "-",
        "item_value":   case.item_value or "-",
        "department":   case.department or "-",
        "claimed_by":   case.claimed_by or "-",
        "claimed_at":   format_thai_datetime(case.claimed_at),
        "alert_type":   getattr(case, "alert_type", "-") or "-",
    }
    return _render_template(template, variables)


def build_claim_notification_payload(case, claim_notify_template: str = ""):
    return [{"type": "text", "text": build_claim_notification_text(case, claim_notify_template)}]


def notify_case_claimed(db, username, case):
    # โหลด claim_notify_template จาก AlertTypeConfig ถ้ามี
    claim_notify_template = ""
    alert_type = getattr(case, "alert_type", None)
    if alert_type:
        try:
            from app.repositories.alert_type_configs import get_by_code
            cfg_row = get_by_code(db, alert_type)
            if cfg_row:
                claim_notify_template = cfg_row.claim_notify_template or ""
        except Exception:
            pass

    payload = build_claim_notification_payload(case, claim_notify_template)
    notify_room_id = getattr(case, "notify_room_id", None)
    return asyncio.run(
        send_with_log(
            db,
            username or "system",
            payload,
            f"claim_case case_key={case.case_key} claimed_by={case.claimed_by or '-'}",
            notify_room_id=notify_room_id,
        )
    )
