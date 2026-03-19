import asyncio
import json
import httpx
from app.core.config import settings

def _base_url():
    return (settings.moph_notify_base_url or '').rstrip('/')

def _send_path():
    path = (settings.moph_notify_send_path or '/api/notify/send').strip()
    return '/' + path.lstrip('/')

def _notify_url():
    return f"{_base_url()}{_send_path()}"

def _sanitize_headers():
    return {
        "client-key_present": bool(settings.moph_notify_client_key),
        "secret-key_present": bool(settings.moph_notify_secret_key),
        "base_url": settings.moph_notify_base_url,
        "send_path": settings.moph_notify_send_path,
        "normalized_url": _notify_url(),
    }

def normalize_result(payload:dict) -> dict:
    if not isinstance(payload, dict):
        return {"raw": payload, "ok": False}
    data = payload.get("data", payload)
    return {
        "ok": payload.get("status") in (200, "200", True) or data is not None,
        "data": data,
        "raw": payload
    }

async def health_check() -> dict:
    return {"status": "configured", "url": _notify_url(), **_sanitize_headers()}

async def send_messages(messages: list[dict], retries:int=3) -> dict:
    last_exc = None
    url = _notify_url()
    headers = {
        "Content-Type": "application/json",
        "client-key": settings.moph_notify_client_key,
        "secret-key": settings.moph_notify_secret_key,
    }
    body = {"messages": messages}
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.post(url, json=body, headers=headers)
                text_body = response.text
                if response.status_code >= 400:
                    raise ValueError(json.dumps({
                        "http_status": response.status_code,
                        "response_text": text_body[:2000],
                        "url": url,
                        **_sanitize_headers(),
                    }, ensure_ascii=False))
                payload = response.json()
                result = normalize_result(payload)
                result["attempt"] = attempt
                return result
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(min(attempt, 3))
    raise last_exc
