import hashlib
import json
from datetime import datetime
from app.repositories.alert_cases import get_by_case_key, create_item, update_item

def _text(value):
    if value is None:
        return ""
    return str(value)

def is_lab_alert_row(row: dict) -> bool:
    required = ["hn", "ptname", "lab_items_name", "lab_order_result"]
    return isinstance(row, dict) and all(k in row for k in required)

def build_case_key(row: dict) -> str:
    raw = "|".join([
        _text(row.get("hn")),
        _text(row.get("lab_items_name")),
        _text(row.get("lab_order_result")),
        _text(row.get("report_date_text") or row.get("report_date")),
        _text(row.get("report_time_text") or row.get("report_time")),
        _text(row.get("cur_dep")),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]

def ensure_case_for_row(db, row: dict):
    if not is_lab_alert_row(row):
        return None
    case_key = build_case_key(row)
    case = get_by_case_key(db, case_key)
    if not case:
        case = create_item(
            db,
            case_key=case_key,
            alert_type="lab_critical",
            patient_hn=_text(row.get("hn")),
            patient_name=_text(row.get("ptname")),
            department=_text(row.get("cur_dep")),
            item_name=_text(row.get("lab_items_name")),
            item_value=_text(row.get("lab_order_result")),
            report_date_text=_text(row.get("report_date_text") or row.get("report_date")),
            report_time_text=_text(row.get("report_time_text") or row.get("report_time")),
            status="NEW",
            source_row_json=json.dumps(row, ensure_ascii=False, default=str),
        )
    return case

def enrich_alert_rows(db, rows, base_url: str):
    out = []
    base_url = (base_url or "").rstrip("/")
    for row in rows or []:
        item = dict(row)
        case = ensure_case_for_row(db, item)
        if case:
            item["case_key"] = case.case_key
            item["claim_url"] = f"{base_url}/alerts/claim?case_key={case.case_key}"
            item["case_status"] = case.status
            item["claimed_by"] = case.claimed_by or ""
            item["claimed_at"] = case.claimed_at.strftime("%Y-%m-%d %H:%M:%S") if case.claimed_at else ""
            item["case_status_text"] = "รับเคสแล้ว" if case.status == "CLAIMED" else "รอรับเคส"
        out.append(item)
    return out

def filter_rows_for_send(rows):
    return [row for row in (rows or []) if str(row.get("case_status", "NEW")) != "CLAIMED"]

def mark_rows_sent(db, rows):
    for row in rows or []:
        case_key = row.get("case_key")
        if not case_key:
            continue
        case = get_by_case_key(db, case_key)
        if not case:
            continue
        now = datetime.utcnow()
        count = int(case.sent_count or 0) + 1
        update_item(
            db,
            case,
            sent_count=count,
            first_sent_at=case.first_sent_at or now,
            last_sent_at=now,
        )

def claim_case(db, case, receiver_name: str):
    now = datetime.utcnow()
    return update_item(db, case, status="CLAIMED", claimed_by=receiver_name, claimed_at=now)
