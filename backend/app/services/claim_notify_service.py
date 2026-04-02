import re
import json
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


def _build_variables(case) -> dict:
    variables: dict = {}
    try:
        src = getattr(case, "source_row_json", None)
        if src:
            variables.update({k: str(v) if v is not None else "-" for k, v in json.loads(src).items()})
    except Exception:
        pass
    variables.update({
        "patient_name": case.patient_name or "-",
        "patient_hn":   case.patient_hn or "-",
        "item_name":    case.item_name or "-",
        "item_value":   case.item_value or "-",
        "department":   case.department or "-",
        "claimed_by":   case.claimed_by or "-",
        "claimed_at":   format_thai_datetime(case.claimed_at),
        "alert_type":   getattr(case, "alert_type", "-") or "-",
    })
    return variables


def _render_str(template: str, variables: dict) -> str:
    return _FIELD_RE.sub(lambda m: str(variables.get(m.group(1), "-")), template)


def _render_flex(flex_template: str, variables: dict) -> list:
    """แทนค่า {field} ใน Flex JSON template แล้วส่งเป็น payload"""
    rendered = _render_str(flex_template, variables)
    contents = json.loads(rendered)
    return [{"type": "flex", "altText": variables.get("patient_name", "รับเคสแล้ว"), "contents": contents}]


def build_claim_notification_payload(case, claim_notify_template: str = "", claim_notify_type: str = "text") -> list:
    variables = _build_variables(case)
    if claim_notify_type == "flex" and claim_notify_template and claim_notify_template.strip():
        try:
            return _render_flex(claim_notify_template.strip(), variables)
        except Exception:
            # fallback to text ถ้า flex render ล้มเหลว
            pass
    template = claim_notify_template.strip() if claim_notify_template else _DEFAULT_TEMPLATE
    return [{"type": "text", "text": _render_str(template, variables)}]


def notify_case_claimed(db, username, case, notify_room_id: int | None = None):
    claim_notify_template = ""
    claim_notify_type = "text"
    alert_type = getattr(case, "alert_type", None)
    if alert_type:
        try:
            from app.repositories.alert_type_configs import get_by_code
            cfg_row = get_by_code(db, alert_type)
            if cfg_row:
                claim_notify_template = cfg_row.claim_notify_template or ""
                claim_notify_type = getattr(cfg_row, "claim_notify_type", "text") or "text"
        except Exception:
            pass

    payload = build_claim_notification_payload(case, claim_notify_template, claim_notify_type)
    # ใช้ room_id จาก claim URL ก่อน (ห้องที่กด claim) ถ้าไม่มีค่อย fallback เป็น case.notify_room_id
    room_id = notify_room_id or getattr(case, "notify_room_id", None)
    return asyncio.run(
        send_with_log(
            db,
            username or "system",
            payload,
            f"claim_case case_key={case.case_key} claimed_by={case.claimed_by or '-'}",
            notify_room_id=room_id,
        )
    )
