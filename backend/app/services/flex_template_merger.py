from app.services.claim_url_builder import build_claim_url
import json
from datetime import datetime
from app.utils.thai_datetime import bangkok_now, format_thai_datetime

def sent_at_text():
    return format_thai_datetime(bangkok_now())

def appointment_date(row:dict):
    return (
        row.get("วันนัด")
        or row.get("appointment_date")
        or row.get("visit_date")
        or row.get("date")
        or "-"
    )

def _replace(obj, mapping):
    if isinstance(obj, dict):
        return {k: _replace(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace(v, mapping) for v in obj]
    if isinstance(obj, str):
        out = obj
        for k, v in mapping.items():
            out = out.replace("{" + k + "}", str(v if v is not None else ""))
        return out
    return obj

def _mapping_for_row(row:dict):
    mapping = dict(row)
    mapping["sent_at"] = sent_at_text()
    mapping["วันนัด"] = appointment_date(row)
    return mapping

def build_flex_payload_from_template_rows(content_text:str, alt_text:str|None, rows:list[dict]):
    parsed = json.loads(content_text)
    if not rows:
        rows = [{}]
    template_type = parsed.get("type")
    if template_type == "bubble":
        bubbles = [fill_missing_claim_urls(_replace(parsed, _mapping_for_row(row)), row) for row in rows[:12]]
        contents = bubbles[0] if len(bubbles) == 1 else {"type":"carousel","contents":bubbles}
    elif template_type == "carousel":
        prototype_bubbles = parsed.get("contents") or []
        if len(prototype_bubbles) == 1:
            proto = prototype_bubbles[0]
            bubbles = [fill_missing_claim_urls(_replace(proto, _mapping_for_row(row)), row) for row in rows[:12]]
            contents = {"type":"carousel","contents":bubbles}
        else:
            contents = _replace(parsed, _mapping_for_row(rows[0]))
    else:
        contents = _replace(parsed, _mapping_for_row(rows[0]))
    return [{
        "type":"flex",
        "altText": alt_text or "BK-Moph Notify Flex Message",
        "contents": contents
    }]


def fill_missing_claim_urls(payload, row=None):
    try:
        claim_url = None
        if isinstance(row, dict):
            claim_url = row.get("claim_url")
            if not claim_url and row.get("case_key"):
                claim_url = build_claim_url(row.get("case_key"))
        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "button":
                    action = node.get("action")
                    if isinstance(action, dict) and action.get("type") == "uri":
                        if not (action.get("uri") or "").strip() and claim_url:
                            action["uri"] = claim_url
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(payload)
    except Exception:
        pass
    return payload
