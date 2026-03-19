import hmac,secrets
def new_token()->str: return secrets.token_urlsafe(24)
def valid(cookie_token:str|None, form_token:str|None)->bool:
    return bool(cookie_token and form_token and hmac.compare_digest(cookie_token, form_token))
