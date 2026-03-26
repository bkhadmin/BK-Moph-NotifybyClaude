from copy import deepcopy

def _is_nonempty_http_url(value):
    return isinstance(value, str) and value.strip().startswith(("http://", "https://"))

def _sanitize_node(node):
    if isinstance(node, dict):
        node = deepcopy(node)

        if node.get("type") == "button":
            action = node.get("action")
            if isinstance(action, dict) and action.get("type") == "uri":
                uri = action.get("uri")
                if not _is_nonempty_http_url(uri):
                    return None

        for key, value in list(node.items()):
            if isinstance(value, dict):
                cleaned = _sanitize_node(value)
                if cleaned is None:
                    del node[key]
                else:
                    node[key] = cleaned
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    cleaned = _sanitize_node(item)
                    if cleaned is not None:
                        cleaned_list.append(cleaned)
                node[key] = cleaned_list

        if node.get("type") == "box" and node.get("contents") == []:
            return None

        if node.get("type") == "bubble":
            if "footer" in node and (not node["footer"] or node["footer"].get("contents") == []):
                node.pop("footer", None)

        return node

    if isinstance(node, list):
        cleaned = []
        for item in node:
            item2 = _sanitize_node(item)
            if item2 is not None:
                cleaned.append(item2)
        return cleaned

    return node

def sanitize_messages(messages):
    cleaned = _sanitize_node(messages)
    if cleaned is None:
        return []
    return cleaned
