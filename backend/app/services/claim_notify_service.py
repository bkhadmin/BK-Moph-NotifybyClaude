import asyncio
from app.services.timezone_utils import format_bangkok
from app.services.send_pipeline import send_with_log

def build_claim_notification_text(case):
    return (
        "รับเคสเรียบร้อย\n\n"
        f"ผู้ป่วย: {case.patient_name or '-'}\n"
        f"HN: {case.patient_hn or '-'}\n"
        f"รายการ: {case.item_name or '-'}\n"
        f"ค่า: {case.item_value or '-'}\n"
        f"แผนก: {case.department or '-'}\n"
        f"ผู้รับเคส: {case.claimed_by or '-'}\n"
        f"เวลารับเคส: {format_bangkok(case.claimed_at)}\n"
        f"สถานะ: รับเคสแล้ว"
    )

def build_claim_notification_payload(case):
    return [{"type": "text", "text": build_claim_notification_text(case)}]

def notify_case_claimed(db, username, case):
    payload = build_claim_notification_payload(case)
    return asyncio.run(
        send_with_log(
            db,
            username or "system",
            payload,
            f"claim_case case_key={case.case_key} claimed_by={case.claimed_by or '-'}",
        )
    )
