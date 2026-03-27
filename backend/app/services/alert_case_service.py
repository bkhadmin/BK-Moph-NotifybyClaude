from app.services.timezone_write import bangkok_now_str, bangkok_now_naive
import hashlib
import json
from datetime import datetime
from app.db.base import Base
from app.db.session import engine
from app.repositories.alert_cases import get_by_case_key, get_by_lab_order_number, create_item, update_item
from app.services.claim_security import build_signed_claim_url

def ensure_tables():
    Base.metadata.create_all(bind=engine)

def _text(value):
    if value is None:
        return ""
    return str(value)

def _normalize_row(row: dict) -> dict:
    """Normalize alternative column names and convert datetime/timedelta to text."""
    from datetime import date, timedelta
    item = dict(row)
    # cur_depart → cur_dep
    if "cur_dep" not in item and "cur_depart" in item:
        item["cur_dep"] = item["cur_depart"]
    # report_date (datetime.date) → report_date_text
    if "report_date_text" not in item or not item["report_date_text"]:
        rd = item.get("report_date")
        if isinstance(rd, date):
            item["report_date_text"] = rd.strftime("%d/%m/%Y")
        elif rd:
            item["report_date_text"] = str(rd)
    # report_time (timedelta seconds) → report_time_text
    if "report_time_text" not in item or not item["report_time_text"]:
        rt = item.get("report_time")
        if isinstance(rt, timedelta):
            total = int(rt.total_seconds())
            hh, rem = divmod(total, 3600)
            mm, ss = divmod(rem, 60)
            item["report_time_text"] = f"{hh:02d}:{mm:02d}"
        elif rt:
            item["report_time_text"] = str(rt)
    return item

# ---------- config helpers ----------

def _default_cfg() -> dict:
    """Fallback config matching the original hardcoded lab_critical behaviour."""
    return {
        "type_code": "lab_critical",
        "required_fields": ["hn", "lab_items_name", "lab_order_result"],
        "key_fields": ["hn", "lab_items_name", "lab_order_result",
                       "report_date_text", "report_time_text", "cur_dep"],
        "field_map": {
            "patient_hn": "hn",
            "patient_name": "ptname",
            "department": "cur_dep",
            "item_name": "lab_items_name",
            "item_value": "lab_order_result",
            "report_date": "report_date_text",
            "report_time": "report_time_text",
            "doctor": "แพทย์ผู้สั่ง",
        },
    }

def _is_alert_row(row: dict, cfg: dict) -> bool:
    required = cfg.get("required_fields") or []
    return isinstance(row, dict) and bool(required) and all(k in row for k in required)

def _build_case_key(row: dict, cfg: dict) -> str:
    key_fields = cfg.get("key_fields") or []
    raw = "|".join([_text(row.get(f)) for f in key_fields])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]

# ---------- backward-compat public helpers ----------

def is_lab_alert_row(row: dict) -> bool:
    return _is_alert_row(row, _default_cfg())

def build_case_key(row: dict) -> str:
    return _build_case_key(row, _default_cfg())

# ---------- main logic ----------

def _extract_lab_order_number(row: dict) -> str | None:
    """Extract lab_order_number from common column name aliases."""
    val = (
        row.get("lab_order_number")
        or row.get("order_number")
        or row.get("lab_order_no")
        or row.get("r.lab_order_number")
    )
    return str(val) if val is not None and str(val).strip() else None


def ensure_case_for_row(db, row: dict, alert_cfg: dict | None = None):
    ensure_tables()
    cfg = alert_cfg or _default_cfg()
    if not _is_alert_row(row, cfg):
        return None

    lab_order_number = _extract_lab_order_number(row)

    # Primary dedup: if lab_order_number present, check it first
    # Same order number = same case regardless of department change
    if lab_order_number:
        existing = get_by_lab_order_number(db, lab_order_number)
        if existing:
            return existing

    # Fallback dedup: case_key hash
    case_key = _build_case_key(row, cfg)
    case = get_by_case_key(db, case_key)
    if case:
        # Backfill lab_order_number if it's now available
        if lab_order_number and not case.lab_order_number:
            from app.repositories.alert_cases import update_item as _upd
            _upd(db, case, lab_order_number=lab_order_number)
        return case

    # Create new case
    fm = cfg.get("field_map", {})
    case = create_item(
        db,
        case_key=case_key,
        lab_order_number=lab_order_number,
        alert_type=cfg.get("type_code", "lab_critical"),
        patient_hn=_text(row.get(fm.get("patient_hn", "hn"))),
        patient_name=_text(row.get(fm.get("patient_name", "ptname"))),
        department=_text(row.get(fm.get("department", "cur_dep"))),
        item_name=_text(row.get(fm.get("item_name", "lab_items_name"))),
        item_value=_text(row.get(fm.get("item_value", "lab_order_result"))),
        report_date_text=_text(row.get(fm.get("report_date", "report_date_text")) or row.get("report_date_text")),
        report_time_text=_text(row.get(fm.get("report_time", "report_time_text")) or row.get("report_time_text")),
        status="NEW",
        source_row_json=json.dumps(row, ensure_ascii=False, default=str),
    )
    return case

def enrich_alert_rows(db, rows, base_url: str, alert_cfg: dict | None = None):
    ensure_tables()
    out = []
    base_url = (base_url or "").rstrip("/")
    cfg = alert_cfg or _default_cfg()
    for row in rows or []:
        item = _normalize_row(dict(row))
        case = ensure_case_for_row(db, item, alert_cfg=cfg)
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
        now = bangkok_now_naive()
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
    now = bangkok_now_naive()
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
