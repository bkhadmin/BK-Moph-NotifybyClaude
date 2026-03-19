import os
import secrets
from urllib.parse import urlencode
import httpx
from app.core.config import settings

def provider_login_url() -> str:
    query = {
        "client_id": settings.health_id_client_id,
        "redirect_uri": settings.health_id_redirect_uri,
        "response_type": "code",
        "state": secrets.token_urlsafe(16),
    }
    return f"{settings.health_id_base_url}/oauth/redirect?{urlencode(query)}"

def _extract_data(payload):
    if not isinstance(payload, dict):
        return {}
    return payload.get("data", payload)

def _pick_token(payload:dict):
    data = _extract_data(payload)
    return data.get("access_token") or data.get("token") or payload.get("access_token") or payload.get("token")

def _provider_token_modes():
    configured = os.getenv("PROVIDER_TOKEN_BY", "Health ID").strip() or "Health ID"
    modes = []
    for item in [configured, "Health ID", "MOPH ID", "health_id", "moph_id"]:
        if item not in modes:
            modes.append(item)
    return modes

def _sanitize_response(status_code:int, text:str, variant:str):
    return {
        "status_code": status_code,
        "variant": variant,
        "response_text": (text or "")[:1200]
    }

async def exchange_health_token(code: str) -> dict:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.post(
            f"{settings.health_id_base_url}/api/v1/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.health_id_redirect_uri,
                "client_id": settings.health_id_client_id,
                "client_secret": settings.health_id_client_secret,
            },
        )
        response.raise_for_status()
        return response.json()

async def _try_provider_variant(client:httpx.AsyncClient, url:str, token_by:str, health_access_token:str, variant:str):
    if variant == "json_body":
        return await client.post(
            url,
            json={
                "client_id": settings.provider_client_id,
                "secret_key": settings.provider_secret_key,
                "token_by": token_by,
                "token": health_access_token,
            },
            headers={"Content-Type": "application/json"},
        )
    if variant == "json_header":
        return await client.post(
            url,
            json={"token_by": token_by, "token": health_access_token},
            headers={
                "Content-Type": "application/json",
                "client-id": settings.provider_client_id,
                "secret-key": settings.provider_secret_key,
            },
        )
    if variant == "form_body":
        return await client.post(
            url,
            data={
                "client_id": settings.provider_client_id,
                "secret_key": settings.provider_secret_key,
                "token_by": token_by,
                "token": health_access_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    return await client.post(
        url,
        json={
            "clientId": settings.provider_client_id,
            "secretKey": settings.provider_secret_key,
            "tokenBy": token_by,
            "token": health_access_token,
        },
        headers={"Content-Type": "application/json"},
    )

async def exchange_provider_token(health_access_token: str) -> dict:
    attempts = []
    variants = ["json_body", "json_header", "form_body", "json_camel"]
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for token_by in _provider_token_modes():
            for variant in variants:
                response = await _try_provider_variant(
                    client,
                    settings.provider_service_token_url,
                    token_by,
                    health_access_token,
                    variant,
                )
                if response.status_code < 400:
                    try:
                        return response.json()
                    except Exception:
                        return {"raw_text": response.text, "variant": variant, "token_by": token_by}
                attempts.append(_sanitize_response(response.status_code, response.text, f"{variant}:{token_by}"))
    raise ValueError({
        "message": "Provider service token exchange failed",
        "endpoint": settings.provider_service_token_url,
        "client_id_present": bool(settings.provider_client_id),
        "secret_key_present": bool(settings.provider_secret_key),
        "attempts": attempts,
    })

async def fetch_provider_profile(provider_access_token: str) -> dict:
    params = {}
    if settings.provider_profile_moph_center_token in (0, 1):
        params["moph_center_token"] = str(settings.provider_profile_moph_center_token)
    if settings.provider_profile_moph_idp_permission in (0, 1):
        params["moph_idp_permission"] = str(settings.provider_profile_moph_idp_permission)
    if settings.provider_profile_position_type in (0, 1):
        params["position_type"] = str(settings.provider_profile_position_type)

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(
            settings.provider_profile_url,
            params=params,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {provider_access_token}",
                "client-id": settings.provider_client_id,
                "secret-key": settings.provider_secret_key,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("data", payload) if isinstance(payload, dict) else {}

async def test_provider_config() -> dict:
    checks = {
        "provider_login_enabled": settings.provider_login_enabled,
        "health_id_base_url": bool(settings.health_id_base_url),
        "health_id_client_id": bool(settings.health_id_client_id),
        "health_id_client_secret": bool(settings.health_id_client_secret),
        "health_id_redirect_uri": bool(settings.health_id_redirect_uri),
        "provider_client_id": bool(settings.provider_client_id),
        "provider_secret_key": bool(settings.provider_secret_key),
        "provider_service_token_url": bool(settings.provider_service_token_url),
        "provider_profile_url": bool(settings.provider_profile_url),
        "provider_token_by_modes": _provider_token_modes(),
    }
    ok = all(bool(v) for k, v in checks.items() if k != "provider_token_by_modes")
    return {"status": "ok" if ok else "incomplete", "checks": checks}

async def exchange_profile(code: str) -> dict:
    if not settings.provider_login_enabled:
        return {
            "account_id": f"acc-{code}",
            "provider_id": f"provider-{code}",
            "username": f"provider-{code}",
            "display_name": "Provider Demo User",
        }

    health_payload = await exchange_health_token(code)
    health_access_token = _pick_token(health_payload)
    if not health_access_token:
        raise ValueError(f"Health ID access_token not found: {health_payload}")

    provider_token_payload = await exchange_provider_token(health_access_token)
    provider_access_token = _pick_token(provider_token_payload)
    if not provider_access_token:
        raise ValueError(f"Provider access_token not found: {provider_token_payload}")

    profile = await fetch_provider_profile(provider_access_token)
    if not isinstance(profile, dict) or not profile:
        raise ValueError("Provider profile response is empty")
    profile["_health_token_payload"] = _extract_data(health_payload)
    profile["_provider_token_payload"] = _extract_data(provider_token_payload)
    return profile
