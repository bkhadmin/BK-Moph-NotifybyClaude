def validate_flex_contents(contents):
    errors = []
    if not isinstance(contents, dict):
        return False, ["contents must be object"]
    ctype = contents.get("type")
    if ctype not in ("bubble", "carousel"):
        errors.append("contents.type must be bubble or carousel")
    if ctype == "bubble":
        if not isinstance(contents.get("body"), dict):
            errors.append("bubble.body is required")
    if ctype == "carousel":
        items = contents.get("contents")
        if not isinstance(items, list) or not items:
            errors.append("carousel.contents must be non-empty list")
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict) or item.get("type") != "bubble":
                    errors.append(f"carousel item {i+1} must be bubble")
    return len(errors) == 0, errors

def validate_flex_message_payload(payload):
    errors = []
    if not isinstance(payload, list) or not payload:
        return False, ["payload must be non-empty list"]
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"message {idx+1} must be object")
            continue
        if item.get("type") != "flex":
            errors.append(f"message {idx+1} type must be flex")
        if not item.get("altText"):
            errors.append(f"message {idx+1} altText is required")
        ok, sub = validate_flex_contents(item.get("contents"))
        if not ok:
            errors.extend([f"message {idx+1}: {x}" for x in sub])
    return len(errors) == 0, errors

def build_minimal_flex_payload():
    return [{
        "type": "flex",
        "altText": "ทดสอบ Flex Message",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "ทดสอบ Flex", "weight": "bold", "size": "lg"},
                    {"type": "text", "text": "ส่งจาก BK-Moph Notify", "wrap": True, "margin": "md"}
                ]
            }
        }
    }]
