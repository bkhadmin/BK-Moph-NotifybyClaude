import json
from sqlalchemy.orm import Session
from app.models.alert_type_config import AlertTypeConfig
from app.services.timezone_write import bangkok_now_naive


def get_all(db: Session):
    return db.query(AlertTypeConfig).order_by(AlertTypeConfig.id.asc()).all()


def get_by_id(db: Session, item_id: int):
    return db.query(AlertTypeConfig).filter(AlertTypeConfig.id == item_id).first()


def get_by_code(db: Session, type_code: str):
    return db.query(AlertTypeConfig).filter(AlertTypeConfig.type_code == type_code).first()


def get_active(db: Session):
    return db.query(AlertTypeConfig).filter(AlertTypeConfig.is_active == 'Y').order_by(AlertTypeConfig.id.asc()).all()


def create_item(db: Session, **kwargs):
    row = AlertTypeConfig(**kwargs)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_item(db: Session, row: AlertTypeConfig, **kwargs):
    for key, value in kwargs.items():
        if hasattr(row, key):
            setattr(row, key, value)
    row.updated_at = bangkok_now_naive()
    db.commit()
    db.refresh(row)
    return row


def delete_item(db: Session, row: AlertTypeConfig):
    db.delete(row)
    db.commit()


def to_cfg_dict(row: AlertTypeConfig) -> dict:
    """Convert DB row to a config dict used by services/renderers."""
    return {
        "type_code": row.type_code,
        "display_name": row.display_name,
        "bubble_title": row.bubble_title or row.display_name,
        "bubble_title_color": row.bubble_title_color or "#b91c1c",
        "required_fields": _parse_json(row.required_fields, []),
        "key_fields": _parse_json(row.key_fields, []),
        "field_map": _parse_json(row.field_map, {}),
    }


def _parse_json(value, default):
    try:
        return json.loads(value or "null") or default
    except Exception:
        return default


DEFAULT_LAB_CRITICAL = {
    "type_code": "lab_critical",
    "display_name": "ผลแล็บวิกฤต (LAB Critical)",
    "bubble_title": "แจ้งเตือนค่า LAB วิกฤต",
    "bubble_title_color": "#b91c1c",
    "required_fields": ["hn", "lab_items_name", "lab_order_result"],
    "key_fields": ["hn", "lab_items_name", "lab_order_result", "report_date_text", "report_time_text", "cur_dep"],
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


def seed_default_lab_critical(db: Session):
    """Ensure the built-in lab_critical config exists."""
    existing = get_by_code(db, "lab_critical")
    if existing:
        return existing
    d = DEFAULT_LAB_CRITICAL
    return create_item(
        db,
        type_code=d["type_code"],
        display_name=d["display_name"],
        bubble_title=d["bubble_title"],
        bubble_title_color=d["bubble_title_color"],
        required_fields=json.dumps(d["required_fields"], ensure_ascii=False),
        key_fields=json.dumps(d["key_fields"], ensure_ascii=False),
        field_map=json.dumps(d["field_map"], ensure_ascii=False),
        is_active='Y',
    )