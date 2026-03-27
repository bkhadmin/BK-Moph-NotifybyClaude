from app.services.timezone_utils import thai_date_str as _thai_date_str

def _get_field(row: dict, field_map: dict, standard_name: str, fallback: str = "") -> str:
    col = field_map.get(standard_name, "")
    val = row.get(col, "") if col else ""
    if not val:
        val = row.get(standard_name, fallback)
    return str(val) if val else fallback

def _fmt_date(value: str) -> str:
    """Convert date string to Thai Buddhist Era format for LINE bubbles."""
    return _thai_date_str(value) if value else ""


def build_claim_alert_carousel(rows: list, cfg: dict) -> list:
    """Generic claim-alert carousel driven by an AlertTypeConfig dict."""
    rows = rows or []
    fm = cfg.get("field_map", {})
    title = cfg.get("bubble_title") or cfg.get("display_name") or "แจ้งเตือน"
    title_color = cfg.get("bubble_title_color") or "#b91c1c"
    alt_text = cfg.get("display_name") or title

    bubbles = []
    for row in rows:
        patient_name = _get_field(row, fm, "patient_name")
        patient_hn   = _get_field(row, fm, "patient_hn")
        department   = _get_field(row, fm, "department")
        item_name    = _get_field(row, fm, "item_name")
        item_value   = _get_field(row, fm, "item_value")
        report_date  = _get_field(row, fm, "report_date")
        report_time  = _get_field(row, fm, "report_time")
        doctor       = _get_field(row, fm, "doctor")

        contents = [
            {"type": "text", "text": title, "weight": "bold", "size": "lg",
             "wrap": True, "color": title_color},
        ]
        if patient_name:
            contents.append({"type": "text", "text": f"ผู้ป่วย {patient_name}",
                              "weight": "bold", "size": "sm", "margin": "md",
                              "wrap": True, "color": "#0f172a"})
        hn_dep = " | ".join(filter(None, [f"HN {patient_hn}" if patient_hn else "", department]))
        if hn_dep:
            contents.append({"type": "text", "text": hn_dep, "size": "xs",
                              "color": "#64748b", "margin": "sm", "wrap": True})
        contents.append({"type": "separator", "margin": "md"})
        if item_name:
            contents.append({"type": "text",
                              "text": f"{item_name} = {item_value}" if item_value else item_name,
                              "weight": "bold", "size": "md", "color": "#dc2626",
                              "margin": "md", "wrap": True})
        if report_date:
            contents.append({"type": "text",
                              "text": f"วันที่ {_fmt_date(report_date)}" + (f" เวลา {report_time}" if report_time else ""),
                              "size": "xs", "color": "#64748b", "margin": "sm", "wrap": True})
        if doctor:
            contents.append({"type": "text", "text": f"แพทย์ผู้สั่ง {doctor}",
                              "size": "xs", "color": "#64748b", "margin": "sm", "wrap": True})

        is_claimed = row.get("case_status") == "CLAIMED"
        contents.append({"type": "text",
                          "text": f"สถานะ {row.get('case_status_text', 'รอรับเคส')}",
                          "size": "xs",
                          "color": "#16a34a" if is_claimed else "#2563eb",
                          "margin": "sm", "wrap": True})

        bubbles.append({
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "contents": contents},
            "footer": {
                "type": "box", "layout": "vertical",
                "contents": [{
                    "type": "button",
                    "style": "secondary" if is_claimed else "primary",
                    "action": {
                        "type": "uri",
                        "label": "ดูข้อมูลเคส" if is_claimed else "รับเคส",
                        "uri": row.get("claim_url", ""),
                    },
                }],
            },
        })

    if not bubbles:
        bubbles = [{
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "contents": [
                {"type": "text", "text": "ไม่พบเคสที่ต้องแจ้งเตือน",
                 "weight": "bold", "size": "md", "wrap": True},
            ]},
        }]

    return [{
        "type": "flex",
        "altText": alt_text,
        "contents": {"type": "carousel", "contents": bubbles[:12]},
    }]


def _default_lab_critical_cfg() -> dict:
    return {
        "type_code": "lab_critical",
        "display_name": "ผลแล็บวิกฤต (LAB Critical)",
        "bubble_title": "แจ้งเตือนค่า LAB วิกฤต",
        "bubble_title_color": "#b91c1c",
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


def build_lab_alert_carousel(rows: list) -> list:
    """Backward-compat wrapper — uses default lab_critical config."""
    return build_claim_alert_carousel(rows, _default_lab_critical_cfg())
