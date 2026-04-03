"""
line_login.py — LINE Login OAuth 2.0 flow
Channel ID / Secret อ่านจาก settings (LINE_LOGIN_CHANNEL_ID, LINE_LOGIN_CHANNEL_SECRET)
"""
import secrets
import httpx
from app.core.config import settings

LINE_AUTH_URL    = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN_URL   = "https://api.line.me/oauth2/v2.1/token"
LINE_PROFILE_URL = "https://api.line.me/v2/profile"
LINE_VERIFY_URL  = "https://api.line.me/oauth2/v2.1/verify"


def get_login_url(redirect_uri: str, state: str) -> str:
    """สร้าง URL สำหรับ redirect ไป LINE Login"""
    from urllib.parse import urlencode
    params = {
        "response_type": "code",
        "client_id":     settings.line_login_channel_id,
        "redirect_uri":  redirect_uri,
        "state":         state,
        "scope":         "profile",
    }
    return LINE_AUTH_URL + "?" + urlencode(params)


async def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """แลก authorization code เป็น access token"""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(LINE_TOKEN_URL, data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  redirect_uri,
            "client_id":     settings.line_login_channel_id,
            "client_secret": settings.line_login_channel_secret,
        })
        resp.raise_for_status()
        return resp.json()


async def get_profile(access_token: str) -> dict:
    """ดึงข้อมูล profile จาก LINE (userId, displayName, pictureUrl)"""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(LINE_PROFILE_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })
        resp.raise_for_status()
        return resp.json()


def generate_state() -> str:
    return secrets.token_urlsafe(16)
