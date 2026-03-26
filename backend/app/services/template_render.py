from app.services.claim_url_builder import build_claim_url
import json

def render_text_template(content:str, variables:dict)->str:
    rendered = content or ''
    for k,v in (variables or {}).items():
        rendered = rendered.replace('{' + str(k) + '}', '' if v is None else str(v))
    return rendered

def build_message_payload(template_type:str, content:str, alt_text:str|None, variables:dict)->dict:
    if template_type == 'text':
        return {"type":"text","text": render_text_template(content, variables)}
    if template_type == 'flex':
        raw = render_text_template(content, variables)
        contents = json.loads(raw)
        return fill_missing_claim_urls({"type":"flex","altText": alt_text or "BK-Moph Notify", "contents": contents}, variables if isinstance(variables, dict) else None)
    if template_type == 'image':
        rendered_url = render_text_template(content, variables)
        return {"type":"image","originalContentUrl": rendered_url, "previewImageUrl": rendered_url}
    return {"type":"text","text": render_text_template(content, variables)}


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
