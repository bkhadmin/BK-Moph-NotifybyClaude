"""
telegram_notify.py — ส่งข้อความ Telegram ผ่าน Bot API
client_key = Bot Token  (เช่น 123456:ABCdef...)
secret_key = Chat ID   (เช่น -1001234567890 สำหรับ group/channel)
"""
import asyncio
import httpx

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _messages_to_text(messages: list) -> str:
    """แปลง LINE message payload เป็น plain text สำหรับ Telegram"""
    parts = []
    for msg in messages:
        msg_type = msg.get("type", "")
        if msg_type == "text":
            parts.append(msg.get("text", ""))
        elif msg_type == "flex":
            # ดึง altText หรือ flatten เนื้อหา
            alt = msg.get("altText", "")
            if alt:
                parts.append(alt)
            else:
                parts.append(_flatten_flex(msg.get("contents", {})))
        else:
            text = msg.get("text") or msg.get("altText") or ""
            if text:
                parts.append(text)
    return "\n\n".join(p for p in parts if p)


def _flatten_flex(contents: dict, depth: int = 0) -> str:
    """แตก Flex JSON เป็น text แบบง่าย"""
    if depth > 5:
        return ""
    lines = []
    if not isinstance(contents, dict):
        return ""
    # ถ้าเป็น carousel ดึงจาก contents[].body
    if contents.get("type") == "carousel":
        for bubble in (contents.get("contents") or []):
            lines.append(_flatten_flex(bubble, depth + 1))
        return "\n".join(lines)
    # ดึงชื่อจาก header
    header = contents.get("header") or {}
    for item in _iter_contents(header):
        t = item.get("text", "")
        if t:
            lines.append(f"*{t}*")
    # ดึงเนื้อหาจาก body
    body = contents.get("body") or {}
    for item in _iter_contents(body):
        t = item.get("text", "")
        if t:
            lines.append(t)
    return "\n".join(lines)


def _iter_contents(node: dict):
    """iterate recursively over all text nodes"""
    if not isinstance(node, dict):
        return
    if node.get("type") == "text" and node.get("text"):
        yield node
    for child in (node.get("contents") or []):
        yield from _iter_contents(child)


async def send_telegram_messages(messages: list, bot_token: str, chat_id: str, retries: int = 3):
    """ส่งข้อความไปยัง Telegram"""
    text = _messages_to_text(messages)
    if not text:
        text = "(ไม่มีข้อความ)"

    url = TELEGRAM_API.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "ok": True,
                    "raw": data,
                    "data": data.get("result"),
                    "attempt": attempt,
                    "channel": "telegram",
                    "chat_id": chat_id,
                }
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(min(attempt, 3))
    raise last_exc
