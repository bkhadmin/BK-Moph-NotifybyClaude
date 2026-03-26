"""
SSO Service — ตรวจสอบ JWT จาก providerlogin แล้วแปลงเป็น profile dict
ที่ upsert_provider_user() รับได้
"""
import jwt
from app.core.config import settings


class SSOError(Exception):
    pass


def verify_sso_token(token: str) -> dict:
    """
    ตรวจสอบ JWT จาก providerlogin
    คืน profile dict ที่ใช้กับ upsert_provider_user() ได้เลย

    JWT payload จาก providerlogin:
      iss       = "providerlogin"
      aud       = "web-apps"
      appId     = settings.sso_app_id
      scope     = "app-access"
      sub       = account_id
      providerId= provider_id
      nameTh    = ชื่อภาษาไทย
      username  = username
      hcode     = รหัสโรงพยาบาล
      hnameTh   = ชื่อโรงพยาบาล
    """
    if not settings.sso_jwt_secret:
        raise SSOError('SSO ยังไม่ได้ตั้งค่า SSO_JWT_SECRET')

    try:
        payload = jwt.decode(
            token,
            settings.sso_jwt_secret,
            algorithms=['HS256'],
            audience='web-apps',
            issuer='providerlogin',
            leeway=15,
        )
    except jwt.ExpiredSignatureError:
        raise SSOError('SSO token หมดอายุ กรุณาเข้าสู่ระบบใหม่จากระบบกลาง')
    except jwt.InvalidTokenError as e:
        raise SSOError(f'SSO token ไม่ถูกต้อง: {e}')

    if payload.get('appId') != settings.sso_app_id:
        raise SSOError('SSO token: appId ไม่ตรงกับระบบนี้')
    if payload.get('scope') != 'app-access':
        raise SSOError('SSO token: scope ไม่ถูกต้อง')

    account_id  = payload.get('sub') or ''
    provider_id = payload.get('providerId') or account_id
    name_th     = payload.get('nameTh') or ''
    username    = payload.get('username') or provider_id
    hcode       = payload.get('hcode') or ''
    hname_th    = payload.get('hnameTh') or ''

    if not account_id:
        raise SSOError('SSO token: ไม่พบข้อมูล account_id')

    # แปลงให้ตรงกับ format ที่ upsert_provider_user() ใช้
    profile = {
        'account_id':  account_id,
        'provider_id': provider_id,
        'username':    username,
        'name_th':     name_th,
        'display_name': name_th or username,
        'hcode':       hcode,
        'hname_th':    hname_th,
        '_sso_source': 'providerlogin',
    }
    return profile
