from app.services.claim_url_builder import build_claim_url
import json
from app.services.flex_table_renderer import build_full_table_flex
from app.services.flex_transform import as_flex_message_payload
from app.services.dynamic_flex_fields import render_dynamic_flex_content
from app.services.lab_alert_renderer import build_lab_alert_carousel

def build_dynamic_template_payload(template_type:str, content:str, alt_text:str|None, rows:list[dict]):
    tt = (template_type or "").strip().lower()
    if tt == "lab_critical_claim":
        return build_lab_alert_carousel(rows or [])

    if tt in ("flex_full_list", "dynamic_full_list"):
        try:
            cfg = json.loads(content or "{}")
        except Exception:
            cfg = {}
        title = cfg.get("title") or "จำนวนผู้ป่วยนัดแยกรายคลินิก"
        chunk_size = int(cfg.get("chunk_size") or 8)
        contents = build_full_table_flex(rows or [], title=title, chunk_size=chunk_size)
        return [{
            "type": "flex",
            "altText": alt_text or title,
            "contents": contents,
        }]
    if tt == "flex_dynamic":
        rendered = render_dynamic_flex_content(content, rows or [])
        if rendered is None:
            return None
        title = "BK-Moph Notify Flex Message"
        try:
            cfg = json.loads(content or "{}")
            if isinstance(cfg, dict):
                title = cfg.get("altText") or title
        except Exception:
            pass
        return [{
            "type": "flex",
            "altText": alt_text or title,
            "contents": rendered,
        }]

    if tt == "flex_top5":
        return as_flex_message_payload(rows or [], "top5")
    if tt == "flex_carousel":
        return as_flex_message_payload(rows or [], "carousel")
    return None


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
