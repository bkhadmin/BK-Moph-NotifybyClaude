import json
import re
from copy import deepcopy

FIELD_RE = re.compile(r"\{([a-zA-Z0-9_ก-๙]+)\}")

def _stringify(value):
    if value is None:
        return ""
    return str(value)

def get_available_fields(rows):
    seen = []
    for row in rows or []:
        if isinstance(row, dict):
            for k in row.keys():
                if k not in seen:
                    seen.append(k)
    return seen

def render_text_template(text, row):
    if not isinstance(text, str):
        return text
    def repl(m):
        key = m.group(1)
        return _stringify((row or {}).get(key, ""))
    return FIELD_RE.sub(repl, text)

def _render_with_repeaters(node, first_row, rows):
    if isinstance(node, dict):
        if node.get("_repeat") == "rows" and "template" in node:
            out = []
            tpl = node["template"]
            for row in rows or []:
                out.append(_render_with_repeaters(deepcopy(tpl), row, rows))
            return out
        out = {}
        for k, v in node.items():
            if k in ("_repeat", "template"):
                continue
            rendered = _render_with_repeaters(v, first_row, rows)
            out[k] = rendered
        return out

    if isinstance(node, list):
        out = []
        for item in node:
            rendered = _render_with_repeaters(item, first_row, rows)
            if isinstance(rendered, list):
                out.extend(rendered)
            else:
                out.append(rendered)
        return out

    if isinstance(node, str):
        return render_text_template(node, first_row)

    return node

def render_dynamic_flex_content(content, rows):
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except Exception:
            return None
    first_row = rows[0] if rows else {}
    return _render_with_repeaters(content, first_row, rows)
