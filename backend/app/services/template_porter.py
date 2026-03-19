import json
from app.repositories.message_templates import create_item

def export_templates_json(rows):
    data = []
    for t in rows:
        data.append({
            "name": t.name,
            "template_type": t.template_type,
            "content": t.content,
            "alt_text": t.alt_text,
            "is_active": getattr(t, "is_active", True),
        })
    return json.dumps(data, ensure_ascii=False, indent=2)

def import_templates_json(db, payload_text:str):
    data = json.loads(payload_text)
    created = 0
    for item in data:
        create_item(
            db,
            item.get("name","Imported Template"),
            item.get("template_type","text"),
            item.get("content",""),
            item.get("alt_text"),
        )
        created += 1
    return {"created": created}
