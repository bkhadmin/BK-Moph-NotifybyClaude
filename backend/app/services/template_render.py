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
        return {"type":"flex","altText": alt_text or "BK-Moph Notify", "contents": contents}
    if template_type == 'image':
        rendered_url = render_text_template(content, variables)
        return {"type":"image","originalContentUrl": rendered_url, "previewImageUrl": rendered_url}
    return {"type":"text","text": render_text_template(content, variables)}
