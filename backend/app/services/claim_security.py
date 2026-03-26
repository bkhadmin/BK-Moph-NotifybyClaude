import hmac
import hashlib
import os
import time

def _secret() -> str:
    return (os.getenv("CLAIM_SIGNING_SECRET") or os.getenv("SECRET_KEY") or "change-me").strip()

def sign_claim(case_key: str, expires_at: int) -> str:
    payload = f"{case_key}:{expires_at}".encode("utf-8")
    return hmac.new(_secret().encode("utf-8"), payload, hashlib.sha256).hexdigest()

def build_signed_claim_url(base_url: str, case_key: str, ttl_seconds: int = 86400) -> str:
    expires_at = int(time.time()) + int(ttl_seconds)
    sig = sign_claim(case_key, expires_at)
    base = (base_url or "").rstrip("/")
    return f"{base}/alerts/claim?case_key={case_key}&expires={expires_at}&sig={sig}"

def verify_claim_signature(case_key: str, expires: str | int | None, sig: str | None) -> bool:
    if not case_key or not expires or not sig:
        return False
    try:
        expires_at = int(expires)
    except Exception:
        return False
    if expires_at < int(time.time()):
        return False
    expected = sign_claim(case_key, expires_at)
    return hmac.compare_digest(expected, str(sig))
