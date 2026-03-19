import re

FORBIDDEN = [
    'insert ','update ','delete ','drop ','alter ','truncate ','create ',
    'grant ','revoke ','into outfile','load_file(','sleep(','benchmark('
]

def strip_sql_comments(sql:str) -> str:
    s = sql or ''
    s = re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)
    s = re.sub(r'--[^\r\n]*', ' ', s)
    s = re.sub(r'#[^\r\n]*', ' ', s)
    return s

def normalize_sql(sql:str)->str:
    s = strip_sql_comments((sql or '').strip())
    s = re.sub(r'\s+', ' ', s).strip()
    if s.endswith(';'):
        s = s[:-1].rstrip()
    return s

def ensure_safe_select(sql:str):
    raw = (sql or '').strip()
    if not raw:
        return False, 'SQL is required'
    s = normalize_sql(raw).lower()
    if not s.startswith('select '):
        return False, 'Only SELECT is allowed'
    for token in FORBIDDEN:
        if token in s:
            return False, f'Forbidden token: {token.strip()}'
    if ';' in s:
        return False, 'Forbidden token: ;'
    return True, 'ok'
