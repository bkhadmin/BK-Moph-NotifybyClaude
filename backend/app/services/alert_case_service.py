from app.services.timezone_write import bangkok_now_str, bangkok_now_naive
import hashlib
import json
from datetime import datetime
from app.db.base import Base
from app.db.session import engine
from app.repositories.alert_cases import get_by_case_key, create_item, update_item
from app.services.claim_security import build_signed_claim_url
from app.services.timezone_utils import utcnow

def ensure_tables():
    Base.metadata.create_all(bind=engine)

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
    ensure_tables()
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
    ensure_tables()
    out = []
    base_url = (base_url or "").rstrip("/")
    for row in rows or []:
        item = dict(row)
        case = ensure_case_for_row(db, item)
        if case:
            item["case_key"] = case.case_key
            item["claim_url"] = build_signed_claim_url(base_url, case.case_key)
            item["case_status"] = case.status
            item["claimed_by"] = case.claimed_by or ""
            item["claimed_at"] = case.claimed_at.strftime("%Y-%m-%d %H:%M:%S") if case.claimed_at else ""
            item["case_status_text"] = "รับเคสแล้ว" if case.status == "CLAIMED" else "รอรับเคส"
        out.append(item)
    return out

def filter_rows_for_send(rows):
    return [row for row in (rows or []) if str(row.get("case_status", "NEW")) != "CLAIMED"]

def mark_rows_sent(db, rows):
    ensure_tables()
    for row in rows or []:
        case_key = row.get("case_key")
        if not case_key:
            continue
        case = get_by_case_key(db, case_key)
        if not case:
            continue
        now = utcnow()
        count = int(case.sent_count or 0) + 1
        update_item(
            db,
            case,
            sent_count=count,
            first_sent_at=case.first_sent_at or now,
            last_sent_at=now,
        )

def claim_case(db, case, receiver_name: str):
    ensure_tables()
    now = utcnow()
    return update_item(db, case, status="CLAIMED", claimed_by=receiver_name, claimed_at=now)

def list_open_alert_cases(db):
    rows = []
    for fn_name in ("get_open_alert_cases", "get_unclaimed_cases", "list_cases", "get_all_cases"):
        fn = globals().get(fn_name)
        if callable(fn):
            try:
                result = fn(db)
                if result is not None:
                    return result
            except Exception:
                pass
    return rows


from datetime import datetime



def mark_alert_case_sent(db, case_key=None, lab_order_number=None):
    try:
        from sqlalchemy import text
        now = bangkok_now_str()
        if lab_order_number:
            db.execute(text("""
                UPDATE alert_cases
                SET
                    first_sent_at = COALESCE(first_sent_at, :now),
                    last_sent_at = :now,
                    sent_count = COALESCE(sent_count, 0) + 1,
                    updated_at = :now
                WHERE lab_order_number = :lab_order_number
            """), {"now": now, "lab_order_number": str(lab_order_number)})
        elif case_key:
            db.execute(text("""
                UPDATE alert_cases
                SET
                    first_sent_at = COALESCE(first_sent_at, :now),
                    last_sent_at = :now,
                    sent_count = COALESCE(sent_count, 0) + 1,
                    updated_at = :now
                WHERE case_key = :case_key
            """), {"now": now, "case_key": case_key})
        else:
            return False
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

def normalize_alert_row_identity(row):
    item = dict(row or {})
    lab_order_number = (
        item.get("lab_order_number")
        or item.get("order_number")
        or item.get("lab_order_no")
        or item.get("r.lab_order_number")
    )
    if lab_order_number is not None:
        item["lab_order_number"] = str(lab_order_number)
    return item
