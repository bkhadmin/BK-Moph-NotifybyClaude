import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

def _base_url():
    return (os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "http://192.168.191.12:8012").rstrip("/")

def _secret():
    return os.getenv("CLAIM_LINK_SECRET") or os.getenv("SECRET_KEY") or "bk-moph-notify-secret"

def build_claim_url(case_key: str, expires_in_seconds: int = 86400) -> str:
    expires = int(time.time()) + int(expires_in_seconds)
    payload = f"{case_key}:{expires}".encode("utf-8")
    sig = hmac.new(_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()
    qs = urlencode({"case_key": case_key, "expires": expires, "sig": sig})
    return f"{_base_url()}/alerts/claim?{qs}"
