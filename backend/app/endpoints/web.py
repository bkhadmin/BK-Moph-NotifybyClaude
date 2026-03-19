import json
from datetime import datetime
from fastapi import APIRouter,Request,Form,Depends,status,HTTPException,UploadFile,File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.csrf import new_token,valid
from app.core.session import create_session,get_session,destroy_session
from app.core.security import verify_password
from app.db.session import get_db
from app.repositories.users import get_by_username,get_by_id,get_all as get_users,upsert_provider_user,update_role
from app.repositories.roles import get_by_code,get_all as get_roles
from app.repositories.permissions import get_all as get_permissions
from app.repositories.access_logs import write_log,get_all as get_access_logs
from app.repositories.ip_bans import get_by_ip,touch_fail,clear_fail
from app.repositories.role_permissions import set_role_permissions,get_permission_codes_for_role
from app.repositories.approved_queries import get_all as get_queries, create_item as create_query, get_by_id as get_query_by_id, update_item as update_query, delete_item as delete_query
from app.repositories.message_templates import get_all as get_templates, create_item as create_template, get_by_id as get_template_by_id, update_item as update_template, delete_item as delete_template, clone_item as clone_template
from app.repositories.schedule_jobs import get_all as get_jobs, create_item as create_job, get_by_id as get_job_by_id, update_item as update_job, delete_item as delete_job
from app.repositories.schedule_job_logs import get_recent as get_schedule_logs
from app.worker_scheduler import run_job_now
from app.repositories.send_logs import get_all as get_send_logs
from app.repositories.media_files import create_item as create_media, get_all as get_media
from app.repositories.delivery_statuses import get_all as get_delivery_statuses
from app.repositories.provider_profiles import get_all as get_provider_profiles, get_by_id as get_provider_profile_by_id, update_profile_manual
from app.repositories.provider_profile_histories import get_all_for_profile
from app.services.rbac import allowed_menu
from app.services.provider_auth import provider_login_url,exchange_profile,test_provider_config
from app.services.hosxp_query import preview_query, test_connection
from app.services.sql_guard import ensure_safe_select
from app.services.template_render import render_text_template, build_message_payload
from app.services.scheduler_service import parse_next_run, scheduler_now
from app.services.media_service import save_resized_image
from app.services.send_pipeline import send_with_log
from app.services.csv_export import to_csv_bytes
from app.services.xlsx_export import to_xlsx_bytes
from app.services.delivery_reconcile import ingest_status_callback
from app.services.pagination import paginate
from app.services.chart_data import counter_from_rows
from app.services.moph_notify import health_check as moph_notify_health_check
from app.services.flex_transform import as_flex_message_payload, detect_mode_and_build
from app.services.flex_validator import validate_flex_message_payload, build_minimal_flex_payload
from app.services.flex_builder_service import build_bubble, template_json_from_bubble
from app.services.template_porter import export_templates_json, import_templates_json
from app.services.flex_template_merger import build_flex_payload_from_template_rows
from app.services.dynamic_template_renderer import build_dynamic_template_payload
from app.services.dynamic_flex_fields import get_available_fields

router=APIRouter()
templates=Jinja2Templates(directory='app/templates')

def client_ip(request:Request)->str:
    return request.headers.get('x-forwarded-for', request.client.host if request.client else 'unknown').split(',')[0].strip()

def get_current_session(request:Request):
    return get_session(request.cookies.get(settings.session_cookie_name))

def _filter_rows(rows, keyword:str):
    if not keyword:
        return rows
    k = keyword.lower()
    out = []
    for row in rows:
        text = ' '.join('' if v is None else str(v) for v in row.values()).lower()
        if k in text:
            out.append(row)
    return out

def require_session(request:Request):
    session = get_current_session(request)
    if not session:
        raise HTTPException(status_code=401, detail='not authenticated')
    return session

def require_menu(db:Session, session:dict, menu_code:str):
    if not allowed_menu(db, session.get('role_id'), menu_code):
        raise HTTPException(status_code=403, detail='forbidden')

def _query_visual_rows(rows):
    out = []
    for row in (rows or [])[:8]:
        if isinstance(row, dict):
            out.append(row)
    return out

def pretty_json(value):
    try:
        if isinstance(value, str):
            value = json.loads(value)
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)

def ctx(request:Request, db:Session, session:dict|None, **extra):
    role_id=session.get('role_id') if session else None
    menus={
        'dashboard':allowed_menu(db,role_id,'dashboard'),
        'users':allowed_menu(db,role_id,'users'),
        'logs':allowed_menu(db,role_id,'logs'),
        'rbac':allowed_menu(db,role_id,'rbac'),
        'notify':allowed_menu(db,role_id,'notify'),
        'queries':allowed_menu(db,role_id,'queries'),
        'templates':allowed_menu(db,role_id,'templates'),
        'schedules':allowed_menu(db,role_id,'schedules'),
        'media':allowed_menu(db,role_id,'media'),
    }
    data={'request':request,'session':session,'menus':menus,'pretty_json':pretty_json}
    data.update(extra)
    return data

def render_login(request:Request, error:str|None=None):
    token=new_token()
    response=templates.TemplateResponse('auth/login.html', {'request':request,'csrf_token':token,'error':error,'provider_login_enabled':settings.provider_login_enabled})
    response.set_cookie(settings.csrf_cookie_name, token, httponly=False, samesite=settings.session_cookie_samesite, path='/')
    return response

@router.get('/health')
def health(): return {'status':'ok','app':settings.app_name}

@router.get('/login')
def login_page(request:Request, error:str|None=None):
    return render_login(request, error)

@router.post('/login')
def login(request:Request, username:str=Form(...), password:str=Form(...), csrf_token:str=Form(...), db:Session=Depends(get_db)):
    ip=client_ip(request)
    ban=get_by_ip(db, ip)
    if ban and ban.is_banned=='Y':
        write_log(db, username, ip, 'login.local', 'blocked', 'IP banned')
        raise HTTPException(status_code=403, detail='IP banned')
    cookie_token=request.cookies.get(settings.csrf_cookie_name)
    if settings.csrf_enabled and not valid(cookie_token, csrf_token):
        write_log(db, username, ip, 'login.local', 'failed', 'csrf validation failed')
        return render_login(request, 'CSRF validation failed')
    user=get_by_username(db, username)
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        row=touch_fail(db, ip, settings.ip_ban_threshold)
        write_log(db, username, ip, 'login.local', 'failed', f'invalid credential fail_count={row.fail_count}')
        return render_login(request, 'Username หรือ Password ไม่ถูกต้อง')
    clear_fail(db, ip)
    sid=create_session({'user_id':user.id,'username':user.username,'display_name':user.display_name,'role_id':user.role_id})
    write_log(db, user.username, ip, 'login.local', 'success', None)
    response=RedirectResponse('/dashboard', status_code=302)
    response.set_cookie(settings.session_cookie_name, sid, httponly=True, samesite=settings.session_cookie_samesite, path='/')
    return response

@router.get('/auth/provider/login')
def provider_login():
    return RedirectResponse(provider_login_url(), status_code=302)

@router.get('/api/v1/auth/provider/callback')
async def provider_callback(request:Request, code:str|None=None, error:str|None=None, db:Session=Depends(get_db)):
    ip=client_ip(request)
    if error:
        write_log(db, None, ip, 'login.provider', 'failed', f'provider_error={error}')
        return render_login(request, f'Provider login failed: {error}')
    if not code:
        write_log(db, None, ip, 'login.provider', 'failed', 'missing authorization code')
        return render_login(request, 'Provider login failed: missing authorization code')
    try:
        profile=await exchange_profile(code)
        default_role=get_by_code(db, 'user')
        user=upsert_provider_user(db, profile, default_role.id if default_role else None)
        sid=create_session({'user_id':user.id,'username':user.username,'display_name':user.display_name,'role_id':user.role_id})
        write_log(db, user.username, ip, 'login.provider', 'success', f"provider_id={profile.get('provider_id')}")
        response=RedirectResponse('/dashboard', status_code=302)
        response.set_cookie(settings.session_cookie_name, sid, httponly=True, samesite=settings.session_cookie_samesite, path='/')
        return response
    except Exception as exc:
        write_log(db, None, ip, 'login.provider', 'failed', str(exc))
        return render_login(request, f'Provider callback error: {exc}')

@router.post('/api/v1/notify/status/callback')
async def notify_status_callback(request:Request, db:Session=Depends(get_db)):
    payload = await request.json()
    result = ingest_status_callback(db, payload)
    return result

@router.get('/dashboard')
def dashboard(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'dashboard')
    return templates.TemplateResponse('admin/dashboard.html', ctx(request, db, session, users=get_users(db), logs=get_access_logs(db), send_logs=get_send_logs(db), jobs=get_jobs(db), media_files=get_media(db), delivery_statuses=get_delivery_statuses(db), provider_profiles=get_provider_profiles(db)))

@router.get('/system/connections')
async def system_connections(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    if not allowed_menu(db, session.get('role_id'), 'logs'):
        raise HTTPException(status_code=403, detail='forbidden')
    try:
        hosxp_result = test_connection()
    except Exception as exc:
        hosxp_result = {"status": "failed", "detail": str(exc)}
    try:
        provider_result = await test_provider_config()
    except Exception as exc:
        provider_result = {"status": "failed", "detail": str(exc)}
    try:
        notify_result = await moph_notify_health_check()
    except Exception as exc:
        notify_result = {"status": "failed", "detail": str(exc)}
    return templates.TemplateResponse('admin/system_connections.html', ctx(request, db, session, hosxp_result=hosxp_result, provider_result=provider_result, notify_result=notify_result))

@router.get('/reports')
def reports_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'logs')
    access_rows = [{"status": x.status} for x in get_access_logs(db)]
    send_rows = [{"status": x.status} for x in get_send_logs(db)]
    delivery_rows = [{"status": x.status} for x in get_delivery_statuses(db)]
    summary = {
        "users": len(get_users(db)),
        "access_logs": len(access_rows),
        "send_logs": len(send_rows),
        "delivery_statuses": len(delivery_rows),
        "provider_profiles": len(get_provider_profiles(db)),
        "media_files": len(get_media(db)),
        "schedules": len(get_jobs(db)),
        "approved_queries": len(get_queries(db)),
        "templates": len(get_templates(db)),
    }
    charts = {
        "access_status": counter_from_rows(access_rows, "status"),
        "send_status": counter_from_rows(send_rows, "status"),
        "delivery_status": counter_from_rows(delivery_rows, "status"),
    }
    return templates.TemplateResponse('admin/reports.html', ctx(request, db, session, summary=summary, charts=charts))

@router.get('/users')
def users_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'users')
    return templates.TemplateResponse('admin/users.html', ctx(request, db, session, users=get_users(db), roles=get_roles(db)))

@router.post('/users/{user_id}/role')
def users_update_role(user_id:int, request:Request, role_id:int=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'users')
    user = get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='user not found')
    update_role(db, user, role_id)
    write_log(db, session.get('username'), client_ip(request), 'user.role.update', 'success', f'user_id={user_id}, role_id={role_id}')
    return RedirectResponse('/users', status_code=302)

@router.get('/profiles')
def profiles_page(request:Request, q:str='', page:int=1, per_page:int=20, db:Session=Depends(get_db)):
    session=require_session(request)
    rows = [{
        "id": x.id, "user_id": x.user_id, "account_id": x.account_id, "provider_id": x.provider_id,
        "name_th": x.name_th, "organization_name": x.organization_name, "organization_code": x.organization_code,
        "position_name": x.position_name, "license_no": x.license_no, "phone": x.phone, "email": x.email
    } for x in get_provider_profiles(db)]
    rows = _filter_rows(rows, q)
    pager = paginate(rows, page=page, per_page=per_page)
    return templates.TemplateResponse('admin/profiles.html', ctx(request, db, session, profile_rows=pager["items"], keyword=q, pager=pager))

@router.get('/profiles/{profile_id}')
def profile_detail_page(profile_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    row = get_provider_profile_by_id(db, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail='profile not found')
    history = get_all_for_profile(db, profile_id)
    return templates.TemplateResponse('admin/profile_detail.html', ctx(request, db, session, profile=row, history_rows=history))

@router.post('/profiles/{profile_id}')
def profile_update_page(profile_id:int, request:Request, name_th:str=Form(''), position_name:str=Form(''), organization_name:str=Form(''), organization_code:str=Form(''), license_no:str=Form(''), phone:str=Form(''), email:str=Form(''), db:Session=Depends(get_db)):
    session=require_session(request)
    row = get_provider_profile_by_id(db, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail='profile not found')
    payload = {
        "name_th": name_th,
        "position_name": position_name,
        "organization_name": organization_name,
        "organization_code": organization_code,
        "license_no": license_no,
        "phone": phone,
        "email": email,
    }
    update_profile_manual(db, row, payload, changed_by=session.get('username'))
    write_log(db, session.get('username'), client_ip(request), 'profile.update', 'success', f'profile_id={profile_id}')
    return RedirectResponse(f'/profiles/{profile_id}', status_code=302)

@router.get('/profiles/export')
def profiles_export(request:Request, q:str='', format:str='csv', db:Session=Depends(get_db)):
    session=require_session(request)
    rows = [{
        "id": x.id, "user_id": x.user_id, "account_id": x.account_id, "provider_id": x.provider_id,
        "name_th": x.name_th, "organization_name": x.organization_name, "organization_code": x.organization_code,
        "position_name": x.position_name, "license_no": x.license_no, "phone": x.phone, "email": x.email
    } for x in get_provider_profiles(db)]
    rows = _filter_rows(rows, q)
    if format == 'xlsx':
        data = to_xlsx_bytes(rows, sheet_name='provider_profiles')
        return Response(content=data, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': 'attachment; filename=provider_profiles.xlsx'})
    data = to_csv_bytes(rows)
    return Response(content=data, media_type='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=provider_profiles.csv'})

@router.get('/logs/access')
def access_logs_page(request:Request, q:str='', page:int=1, per_page:int=20, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'logs')
    access_rows = [{"actor": x.actor, "ip_address": x.ip_address, "action": x.action, "status": x.status, "detail": x.detail} for x in get_access_logs(db)]
    send_rows = [{"id": x.id, "actor": x.actor, "channel": x.channel, "status": x.status, "retry_count": x.retry_count, "detail": x.detail} for x in get_send_logs(db)]
    delivery_rows = [{"send_log_id": x.send_log_id, "external_message_id": x.external_message_id, "status": x.status, "provider_status": x.provider_status, "detail": x.detail} for x in get_delivery_statuses(db)]
    access_rows = _filter_rows(access_rows, q)
    send_rows = _filter_rows(send_rows, q)
    delivery_rows = _filter_rows(delivery_rows, q)
    access_pager = paginate(access_rows, page=page, per_page=per_page)
    send_pager = paginate(send_rows, page=page, per_page=per_page)
    delivery_pager = paginate(delivery_rows, page=page, per_page=per_page)
    return templates.TemplateResponse('admin/access_logs.html', ctx(request, db, session, logs=access_pager["items"], send_logs=send_pager["items"], delivery_statuses=delivery_pager["items"], keyword=q, pager=access_pager))

@router.get('/logs/export/{kind}')
def logs_export(kind:str, request:Request, q:str='', format:str='csv', db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'logs')
    if kind == 'access':
        rows = [{"actor": x.actor, "ip_address": x.ip_address, "action": x.action, "status": x.status, "detail": x.detail} for x in get_access_logs(db)]
    elif kind == 'send':
        rows = [{"id": x.id, "actor": x.actor, "channel": x.channel, "status": x.status, "retry_count": x.retry_count, "detail": x.detail} for x in get_send_logs(db)]
    else:
        rows = [{"send_log_id": x.send_log_id, "external_message_id": x.external_message_id, "status": x.status, "provider_status": x.provider_status, "detail": x.detail} for x in get_delivery_statuses(db)]
    rows = _filter_rows(rows, q)
    if format == 'xlsx':
        data = to_xlsx_bytes(rows, sheet_name=f'{kind}_logs')
        return Response(content=data, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition': f'attachment; filename={kind}_logs.xlsx'})
    data = to_csv_bytes(rows)
    return Response(content=data, media_type='text/csv; charset=utf-8', headers={'Content-Disposition': f'attachment; filename={kind}_logs.csv'})

@router.get('/queries')
def queries_page(request:Request, edit_id:int|None=None, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    edit_row = get_query_by_id(db, edit_id) if edit_id else None
    return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=None, hosxp_test=None, edit_row=edit_row))

@router.post('/queries')
def create_query_page(request:Request, name:str=Form(...), sql_text:str=Form(...), max_rows:int=Form(100), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    ok, reason = ensure_safe_select(sql_text)
    if ok:
        create_query(db, name, sql_text, max_rows)
        write_log(db, session.get('username'), client_ip(request), 'query.create', 'success', name)
        return RedirectResponse('/queries', status_code=302)
    return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=reason, hosxp_test=None, edit_row=None))

@router.post('/queries/{query_id}/update')
def update_query_page(query_id:int, request:Request, name:str=Form(...), sql_text:str=Form(...), max_rows:int=Form(100), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    row = get_query_by_id(db, query_id)
    if not row:
        raise HTTPException(status_code=404, detail='query not found')
    ok, reason = ensure_safe_select(sql_text)
    if ok:
        update_query(db, row, name, sql_text, max_rows)
        write_log(db, session.get('username'), client_ip(request), 'query.update', 'success', f'query_id={query_id}')
        return RedirectResponse('/queries', status_code=302)
    return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=reason, hosxp_test=None, edit_row=row))

@router.post('/queries/{query_id}/delete')
def delete_query_page(query_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    row = get_query_by_id(db, query_id)
    if not row:
        raise HTTPException(status_code=404, detail='query not found')
    delete_query(db, row)
    write_log(db, session.get('username'), client_ip(request), 'query.delete', 'success', f'query_id={query_id}')
    return RedirectResponse('/queries', status_code=302)

@router.post('/queries/preview')
def preview_query_page(request:Request, sql_text:str=Form(...), max_rows:int=Form(20), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    try:
        preview = preview_query(sql_text, max_rows=max_rows)
        write_log(db, session.get('username'), client_ip(request), 'query.preview', 'success', f"rows={preview['row_count']}")
        return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=preview, error=None, hosxp_test=None, edit_row=None))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'query.preview', 'failed', str(exc))
        return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=str(exc), hosxp_test=None, edit_row=None))

@router.post('/queries/test-connection')
def query_test_connection(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'queries')
    try:
        result = test_connection()
        write_log(db, session.get('username'), client_ip(request), 'query.test_connection', 'success', json.dumps(result, ensure_ascii=False))
        return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=None, hosxp_test=result, edit_row=None))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'query.test_connection', 'failed', str(exc))
        return templates.TemplateResponse('admin/queries.html', ctx(request, db, session, queries=get_queries(db), preview=None, error=None, hosxp_test={"status":"failed","detail":str(exc)}, edit_row=None))

@router.get('/templates')
def templates_page(request:Request, edit_id:int|None=None, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    flex_sample = '{"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"สวัสดี {name}"},{"type":"text","text":"หน่วยงาน {organization_name}","size":"sm"}]}}'
    edit_row = get_template_by_id(db, edit_id) if edit_id else None
    return templates.TemplateResponse('admin/templates.html', ctx(request, db, session, message_templates=get_templates(db), render_result=None, media_files=get_media(db), flex_sample=flex_sample, edit_row=edit_row))

@router.post('/templates')
def create_template_page(request:Request, name:str=Form(...), template_type:str=Form(...), content:str=Form(...), alt_text:str=Form(''), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    create_template(db, name, template_type, content, alt_text or None)
    write_log(db, session.get('username'), client_ip(request), 'template.create', 'success', name)
    return RedirectResponse('/templates', status_code=302)

@router.post('/templates/{template_id}/update')
def update_template_page(template_id:int, request:Request, name:str=Form(...), template_type:str=Form(...), content:str=Form(...), alt_text:str=Form(''), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    row = get_template_by_id(db, template_id)
    if not row:
        raise HTTPException(status_code=404, detail='template not found')
    update_template(db, row, name, template_type, content, alt_text or None)
    write_log(db, session.get('username'), client_ip(request), 'template.update', 'success', f'template_id={template_id}')
    return RedirectResponse('/templates', status_code=302)

@router.post('/templates/{template_id}/delete')
def delete_template_page(template_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    row = get_template_by_id(db, template_id)
    if not row:
        raise HTTPException(status_code=404, detail='template not found')
    delete_template(db, row)
    write_log(db, session.get('username'), client_ip(request), 'template.delete', 'success', f'template_id={template_id}')
    return RedirectResponse('/templates', status_code=302)

@router.post('/templates/render')
def render_template_page(request:Request, content:str=Form(...), variables_json:str=Form('{}'), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    variables = json.loads(variables_json or '{}')
    render_result = render_text_template(content, variables)
    write_log(db, session.get('username'), client_ip(request), 'template.render', 'success', None)
    flex_sample = '{"type":"bubble","body":{"type":"box","layout":"vertical","contents":[{"type":"text","text":"สวัสดี {name}"},{"type":"text","text":"หน่วยงาน {organization_name}","size":"sm"}]}}'
    return templates.TemplateResponse('admin/templates.html', ctx(request, db, session, message_templates=get_templates(db), render_result=render_result, media_files=get_media(db), flex_sample=flex_sample, edit_row=None))

@router.get('/media')
def media_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'media')
    return templates.TemplateResponse('admin/media.html', ctx(request, db, session, media_files=get_media(db)))

@router.post('/media')
async def media_upload(request:Request, image:UploadFile=File(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'media')
    content = await image.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail='File too large')
    saved = save_resized_image(content, image.filename or 'upload.jpg', image.content_type)
    create_media(db, image.filename or saved['stored_name'], saved['stored_name'], saved['mime_type'], saved['width'], saved['height'], saved['public_url'])
    write_log(db, session.get('username'), client_ip(request), 'media.upload', 'success', saved['public_url'])
    return RedirectResponse('/media', status_code=302)

@router.get('/notify/test')
def notify_page(request:Request, flex_json:str|None=None, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    default_flex = flex_json or json.dumps({
        "type":"bubble",
        "body":{"type":"box","layout":"vertical","contents":[
            {"type":"text","text":"หัวข้อ", "weight":"bold", "size":"lg"},
            {"type":"text","text":"รายละเอียดข้อความ", "wrap":True, "margin":"md"}
        ]}
    }, ensure_ascii=False, indent=2)
    return templates.TemplateResponse('admin/notify_test.html', ctx(request, db, session, result=None, send_error=None, template_payload=None, data_rows=None, query_visual_rows=None, approved_queries=get_queries(db), message_templates=get_templates(db), media_files=get_media(db), flex_json=default_flex))

@router.post('/notify/test')
async def notify_send(request:Request, message_text:str=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    payload=[{"type":"text","text":message_text}]
    try:
        result, _ = await send_with_log(db, session.get('username'), payload, 'manual text send')
        write_log(db, session.get('username'), client_ip(request), 'notify.send', 'success', 'manual text send')
        return templates.TemplateResponse('admin/notify_test.html', ctx(request, db, session, result=result, send_error=None, template_payload=payload, data_rows=None, query_visual_rows=None, approved_queries=get_queries(db), message_templates=get_templates(db), media_files=get_media(db), flex_json=None))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'notify.send', 'failed', str(exc))
        return templates.TemplateResponse('admin/notify_test.html', ctx(request, db, session, result=None, send_error=str(exc), template_payload=payload, data_rows=None, query_visual_rows=None, approved_queries=get_queries(db), message_templates=get_templates(db), media_files=get_media(db), flex_json=None))

@router.post('/notify/send-flex')
async def notify_send_flex(request:Request, flex_json:str=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    try:
        contents = json.loads(flex_json)
        payload=[{"type":"flex","altText":"Flex Message Preview","contents":contents}]
        ok, errors = validate_flex_message_payload(payload)
        if not ok:
            raise ValueError("Flex validation failed: " + "; ".join(errors))
        result, _ = await send_with_log(db, session.get('username'), payload, 'manual flex send')
        write_log(db, session.get('username'), client_ip(request), 'notify.send.flex', 'success', 'manual flex send')
        return templates.TemplateResponse('admin/notify_test.html', ctx(request, db, session, result=result, send_error=None, validation_errors=None, template_payload=payload, data_rows=None, query_visual_rows=None, approved_queries=get_queries(db), message_templates=get_templates(db), media_files=get_media(db), flex_json=flex_json))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'notify.send.flex', 'failed', str(exc))
        return templates.TemplateResponse('admin/notify_test.html', ctx(request, db, session, result=None, send_error=str(exc), validation_errors=None, template_payload=None, data_rows=None, query_visual_rows=None, approved_queries=get_queries(db), message_templates=get_templates(db), media_files=get_media(db), flex_json=flex_json))

@router.post('/notify/flex-builder')
def notify_flex_builder(
    request:Request,
    preset_mode:str=Form('single'),
    title:str=Form('หัวข้อ'),
    subtitle:str=Form(''),
    body_text:str=Form('รายละเอียด'),
    button_label:str=Form(''),
    button_url:str=Form(''),
    hero_image_url:str=Form(''),
    title_color:str=Form('#0f172a'),
    subtitle_color:str=Form('#64748b'),
    body_color:str=Form('#334155'),
    accent_color:str=Form('#2563eb'),
    title_size:str=Form('lg'),
    body_size:str=Form('md'),
    save_as_template:str=Form('0'),
    template_name:str=Form(''),
    db:Session=Depends(get_db)
):
    session=require_session(request)
    require_menu(db, session, 'notify')

    if preset_mode == 'top5':
        bubble = {
            "type":"bubble",
            "body":{"type":"box","layout":"vertical","contents":[
                {"type":"text","text": title or "Top 5 นัดหมายวันนี้","weight":"bold","size":"lg","wrap":True, "color": title_color},
                {"type":"text","text": subtitle or "ส่งเมื่อ {sent_at}","size":"sm","color":subtitle_color,"wrap":True,"margin":"md"},
                {"type":"separator","margin":"md"},
                {"type":"text","text":"1. {row1_clinic_name} - {row1_total_appointment} ราย","wrap":True,"margin":"md","color":body_color},
                {"type":"text","text":"2. {row2_clinic_name} - {row2_total_appointment} ราย","wrap":True,"margin":"sm","color":body_color},
                {"type":"text","text":"3. {row3_clinic_name} - {row3_total_appointment} ราย","wrap":True,"margin":"sm","color":body_color},
                {"type":"text","text":"4. {row4_clinic_name} - {row4_total_appointment} ราย","wrap":True,"margin":"sm","color":body_color},
                {"type":"text","text":"5. {row5_clinic_name} - {row5_total_appointment} ราย","wrap":True,"margin":"sm","color":body_color}
            ]}
        }
        contents = bubble
        save_template_type = 'flex_top5'
        save_template_content = json.dumps({'title': title or 'Top 5 นัดหมายวันนี้'}, ensure_ascii=False)
        save_alt_text = title.strip() or 'BK-Moph Notify Flex Message'
    elif preset_mode == 'full_list':
        preview_bubble = {
            "type":"bubble",
            "body":{"type":"box","layout":"vertical","contents":[
                {"type":"text","text": title or "จำนวนผู้ป่วยนัดแยกรายคลินิก","weight":"bold","size":"lg","wrap":True, "color": title_color},
                {"type":"text","text": subtitle or "วันที่ {วันนัด}","size":"sm","color":subtitle_color,"wrap":True,"margin":"md"},
                {"type":"text","text":"ส่งเมื่อ {sent_at}","size":"sm","color":"#64748b","wrap":True,"margin":"sm"},
                {"type":"separator","margin":"md"},
                {"type":"text","text":"คลินิก / แผนก / จำนวนผู้ป่วย จะถูกสร้างอัตโนมัติจาก Query ทุกแถว","size":"sm","color":body_color,"wrap":True,"margin":"md"}
            ]}
        }
        contents = preview_bubble
        save_template_type = 'flex_full_list'
        save_template_content = json.dumps({
            'title': title or 'จำนวนผู้ป่วยนัดแยกรายคลินิก',
            'chunk_size': 8
        }, ensure_ascii=False)
        save_alt_text = title.strip() or 'จำนวนผู้ป่วยนัดแยกรายคลินิก'
    else:
        bubble = build_bubble(
            title=title, subtitle=subtitle, body_text=body_text, hero_image_url=hero_image_url,
            button_label=button_label, button_url=button_url,
            title_color=title_color, subtitle_color=subtitle_color, body_color=body_color,
            accent_color=accent_color, title_size=title_size, body_size=body_size
        )
        if preset_mode == 'summary':
            bubble["body"]["contents"].append({"type":"separator","margin":"md"})
            bubble["body"]["contents"].append({"type":"text","text":"BK-Moph Notify","size":"xs","color":"#94a3b8","align":"center","margin":"md"})
        contents = {"type":"carousel","contents":[bubble]} if preset_mode == 'carousel' else bubble
        save_template_type = 'flex_carousel' if preset_mode == 'carousel' else 'flex'
        save_template_content = json.dumps(contents, ensure_ascii=False)
        save_alt_text = title.strip() or 'BK-Moph Notify Flex Message'

    flex_json = json.dumps(contents, ensure_ascii=False, indent=2)

    if save_as_template == '1' and (template_name or '').strip():
        create_template(db, template_name.strip(), save_template_type, save_template_content, save_alt_text)
        write_log(db, session.get('username'), client_ip(request), 'template.create.from_flex_builder', 'success', template_name.strip())

    return templates.TemplateResponse('admin/notify_test.html', ctx(
        request, db, session,
        result=None, send_error=None, validation_errors=None,
        template_payload=None, data_rows=None, query_visual_rows=None,
        approved_queries=get_queries(db), message_templates=get_templates(db),
        media_files=get_media(db), flex_json=flex_json
    ))

@router.post('/notify/validate-flex')
def notify_validate_flex(request:Request, flex_json:str=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    validation_errors = None
    try:
        contents = json.loads(flex_json)
        payload=[{"type":"flex","altText":"Flex Message Preview","contents":contents}]
        ok, errors = validate_flex_message_payload(payload)
        validation_errors = [] if ok else errors
    except Exception as exc:
        validation_errors = [str(exc)]
    return templates.TemplateResponse('admin/notify_test.html', ctx(
        request, db, session,
        result=None, send_error=None, validation_errors=validation_errors,
        template_payload=None, data_rows=None, query_visual_rows=None,
        approved_queries=get_queries(db), message_templates=get_templates(db),
        media_files=get_media(db), flex_json=flex_json
    ))

@router.post('/notify/send-minimal-flex')
async def notify_send_minimal_flex(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    payload = build_minimal_flex_payload()
    try:
        result, _ = await send_with_log(db, session.get('username'), payload, 'minimal flex send')
        write_log(db, session.get('username'), client_ip(request), 'notify.send.minimal_flex', 'success', 'minimal flex send')
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=result, send_error=None, validation_errors=[],
            template_payload=payload, data_rows=None, query_visual_rows=None,
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(payload[0]["contents"], ensure_ascii=False, indent=2)
        ))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'notify.send.minimal_flex', 'failed', str(exc))
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=None, send_error=str(exc), validation_errors=None,
            template_payload=payload, data_rows=None, query_visual_rows=None,
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(payload[0]["contents"], ensure_ascii=False, indent=2)
        ))

@router.post('/notify/auto-flex-preview')
def notify_auto_flex_preview(
    request:Request,
    approved_query_id:int=Form(...),
    auto_mode:str=Form('single'),
    db:Session=Depends(get_db)
):
    session=require_session(request)
    require_menu(db, session, 'notify')
    q = get_query_by_id(db, approved_query_id)
    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = data['rows']
    contents = detect_mode_and_build(rows, auto_mode)
    flex_json = json.dumps(contents, ensure_ascii=False, indent=2)
    return templates.TemplateResponse('admin/notify_test.html', ctx(
        request, db, session,
        result=None, send_error=None, template_payload=None,
        data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
        approved_queries=get_queries(db), message_templates=get_templates(db),
        media_files=get_media(db), flex_json=flex_json
    ))

@router.post('/notify/auto-flex-send')
async def notify_auto_flex_send(
    request:Request,
    approved_query_id:int=Form(...),
    auto_mode:str=Form('single'),
    db:Session=Depends(get_db)
):
    session=require_session(request)
    require_menu(db, session, 'notify')
    q = get_query_by_id(db, approved_query_id)
    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = data['rows']
    payload = as_flex_message_payload(rows, auto_mode)
    try:
        result, _ = await send_with_log(db, session.get('username'), payload, f'auto flex from query {q.id} mode={auto_mode}')
        write_log(db, session.get('username'), client_ip(request), 'notify.send.auto_flex', 'success', f'query_id={q.id} mode={auto_mode}')
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=result, send_error=None, template_payload=payload,
            data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(payload[0]["contents"], ensure_ascii=False, indent=2)
        ))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'notify.send.auto_flex', 'failed', str(exc))
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=None, send_error=str(exc), template_payload=payload,
            data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(payload[0]["contents"], ensure_ascii=False, indent=2)
        ))


@router.post('/notify/preview')
def notify_preview(request:Request, approved_query_id:int=Form(...), message_template_id:int=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    q = get_query_by_id(db, approved_query_id)
    t = get_template_by_id(db, message_template_id)
    if not q or not t:
        raise HTTPException(status_code=404, detail='query or template not found')
    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = enrich_alert_rows(db, data['rows'], str(request.base_url).rstrip('/'))
    rows = filter_rows_for_send(rows)
    dynamic_payload = build_dynamic_template_payload(t.template_type, t.content, t.alt_text, rows)
    if dynamic_payload is not None:
        payload = dynamic_payload
    elif t.template_type == 'flex':
        payload = build_flex_payload_from_template_rows(t.content, t.alt_text, rows)
    else:
        first_row = rows[0] if rows else {}
        payload = build_message_payload(t.template_type, t.content, t.alt_text, first_row)
    return templates.TemplateResponse('admin/notify_test.html', ctx(
        request, db, session,
        result=None, send_error=None, validation_errors=None,
        template_payload=payload, data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
        approved_queries=get_queries(db), message_templates=get_templates(db),
        media_files=get_media(db), flex_json=json.dumps(payload[0]["contents"], ensure_ascii=False, indent=2) if isinstance(payload, list) and payload and payload[0].get("type") == "flex" else None
    ))

@router.post('/notify/send-from-template')
async def notify_send_from_template(request:Request, approved_query_id:int=Form(...), message_template_id:int=Form(...), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    q = get_query_by_id(db, approved_query_id)
    t = get_template_by_id(db, message_template_id)
    if not q or not t:
        raise HTTPException(status_code=404, detail='query or template not found')
    data = preview_query(q.sql_text, max_rows=q.max_rows)
    rows = enrich_alert_rows(db, data['rows'], str(request.base_url).rstrip('/'))
    rows = filter_rows_for_send(rows)
    dynamic_payload = build_dynamic_template_payload(t.template_type, t.content, t.alt_text, rows)
    if dynamic_payload is not None:
        messages = dynamic_payload
    elif t.template_type == 'flex':
        messages = build_flex_payload_from_template_rows(t.content, t.alt_text, rows)
    else:
        messages = [build_message_payload(t.template_type, t.content, t.alt_text, row) for row in rows]
    try:
        result, _ = await send_with_log(db, session.get('username'), messages, f'approved_query_id={q.id}, template_id={t.id}')
        mark_rows_sent(db, rows)
        write_log(db, session.get('username'), client_ip(request), 'notify.send.template', 'success', f'rows={len(rows)}')
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=result, send_error=None, validation_errors=None,
            template_payload=messages, data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(messages[0]["contents"], ensure_ascii=False, indent=2) if isinstance(messages, list) and messages and messages[0].get("type") == "flex" else None
        ))
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'notify.send.template', 'failed', str(exc))
        return templates.TemplateResponse('admin/notify_test.html', ctx(
            request, db, session,
            result=None, send_error=str(exc), validation_errors=None,
            template_payload=messages, data_rows=rows[:10], query_visual_rows=_query_visual_rows(rows),
            approved_queries=get_queries(db), message_templates=get_templates(db),
            media_files=get_media(db), flex_json=json.dumps(messages[0]["contents"], ensure_ascii=False, indent=2) if isinstance(messages, list) and messages and messages[0].get("type") == "flex" else None
        ))


@router.get('/schedules')
def schedules_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    edit_id = request.query_params.get('edit_id')
    edit_job = get_job_by_id(db, int(edit_id)) if edit_id else None
    form_values = {}
    if edit_job:
        try:
            cfg = json.loads(edit_job.payload_json or '{}')
        except Exception:
            cfg = {}
        form_values = {
            'id': edit_job.id,
            'name': edit_job.name,
            'schedule_type': edit_job.schedule_type,
            'cron_value': edit_job.cron_value or '',
            'interval_minutes': str(edit_job.interval_minutes or ''),
            'approved_query_id': edit_job.approved_query_id or '',
            'message_template_id': edit_job.message_template_id or '',
            'is_active': edit_job.is_active,
            'retry_limit': str(cfg.get('retry_limit', 3)),
        }
    return templates.TemplateResponse('admin/schedules.html', ctx(request, db, session, jobs=get_jobs(db), approved_queries=get_queries(db), message_templates=get_templates(db), form_error=None, form_values=form_values))


@router.post('/schedules')
def schedules_create(
    request:Request,
    schedule_id:str=Form(''),
    name:str=Form(...),
    schedule_type:str=Form(...),
    cron_value:str=Form(''),
    interval_minutes:str=Form(''),
    approved_query_id:int|None=Form(None),
    message_template_id:int|None=Form(None),
    is_active:str=Form('Y'),
    retry_limit:str=Form('3'),
    db:Session=Depends(get_db)
):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    try:
        normalized_cron = (cron_value or '').strip()
        normalized_interval = None
        if str(interval_minutes or '').strip() != '':
            normalized_interval = int(str(interval_minutes).strip())
        next_run_at = parse_next_run(schedule_type, normalized_cron or None, normalized_interval, base=scheduler_now())
        payload_json = json.dumps({'retry_limit': int(str(retry_limit or '3').strip() or '3'), 'retry_count': 0}, ensure_ascii=False)
        if str(schedule_id or '').strip():
            row = get_job_by_id(db, int(schedule_id))
            if not row:
                raise ValueError('schedule ไม่พบ')
            update_job(
                db,
                row,
                name=name.strip(),
                schedule_type=schedule_type,
                cron_value=normalized_cron or None,
                interval_minutes=normalized_interval,
                approved_query_id=approved_query_id,
                message_template_id=message_template_id,
                next_run_at=next_run_at,
                is_active=is_active,
                payload_json=payload_json,
            )
        else:
            create_job(
                db,
                name=name.strip(),
                schedule_type=schedule_type,
                cron_value=normalized_cron or None,
                interval_minutes=normalized_interval,
                approved_query_id=approved_query_id,
                message_template_id=message_template_id,
                next_run_at=next_run_at,
                is_active=is_active,
                payload_json=payload_json,
            )
        write_log(db, session.get('username'), client_ip(request), 'schedule.create', 'success', f'name={name}, type={schedule_type}')
        return RedirectResponse('/schedules', status_code=302)
    except Exception as exc:
        write_log(db, session.get('username'), client_ip(request), 'schedule.create', 'failed', str(exc))
        return templates.TemplateResponse(
            'admin/schedules.html',
            ctx(
                request, db, session,
                jobs=get_jobs(db),
                approved_queries=get_queries(db),
                message_templates=get_templates(db),
                form_error=str(exc),
                form_values={
                    'id': schedule_id,
                    'name': name,
                    'schedule_type': schedule_type,
                    'cron_value': cron_value,
                    'interval_minutes': str(interval_minutes or '').strip(),
                    'approved_query_id': approved_query_id or '',
                    'message_template_id': message_template_id or '',
                    'is_active': is_active,
                    'retry_limit': retry_limit,
                }
            ),
            status_code=400
        )


@router.get('/rbac')
def rbac_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'rbac')
    roles=get_roles(db); permissions=get_permissions(db); role_map={r.id:get_permission_codes_for_role(db,r.id) for r in roles}
    return templates.TemplateResponse('admin/rbac.html', ctx(request, db, session, roles=roles, permissions=permissions, role_map=role_map))

@router.post('/rbac/role/{role_id}')
def rbac_update(role_id:int, request:Request, permission_ids:list[int]=Form(default=[]), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'rbac')
    set_role_permissions(db, role_id, permission_ids)
    write_log(db, session.get('username'), client_ip(request), 'rbac.update', 'success', f'role_id={role_id}')
    return RedirectResponse('/rbac', status_code=302)


@router.post('/templates/{template_id}/clone')
def clone_template_page(template_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    row = get_template_by_id(db, template_id)
    if not row:
        raise HTTPException(status_code=404, detail='template not found')
    clone_template(db, row)
    write_log(db, session.get('username'), client_ip(request), 'template.clone', 'success', f'template_id={template_id}')
    return RedirectResponse('/templates', status_code=302)

@router.get('/templates/export')
def export_templates_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    payload = export_templates_json(get_templates(db))
    return Response(content=payload, media_type='application/json; charset=utf-8', headers={'Content-Disposition':'attachment; filename=message_templates.json'})

@router.post('/templates/import')
async def import_templates_page(request:Request, import_payload:str=Form(''), db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    result = import_templates_json(db, import_payload)
    write_log(db, session.get('username'), client_ip(request), 'template.import', 'success', str(result))
    return RedirectResponse('/templates', status_code=302)

@router.get('/schedules/{job_id}/delete')
def schedule_delete_get(job_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    row = get_job_by_id(db, job_id)
    if row:
        delete_job(db, row)
    return RedirectResponse('/schedules', status_code=302)

@router.post('/schedules/{job_id}/delete')
def schedule_delete(job_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    row = get_job_by_id(db, job_id)
    if row:
        delete_job(db, row)
    return RedirectResponse('/schedules', status_code=302)

@router.post('/schedules/{job_id}/run-now')
def schedule_run_now(job_id:int, request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    run_job_now(job_id)
    return RedirectResponse('/scheduler-monitor', status_code=302)

@router.get('/scheduler-monitor')
def scheduler_monitor_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'schedules')
    return templates.TemplateResponse('admin/scheduler_monitor.html', ctx(
        request, db, session,
        jobs=get_jobs(db),
        schedule_logs=get_schedule_logs(db, 100)
    ))


@router.get('/templates/dynamic-flex-builder')
def dynamic_flex_builder_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'templates')
    return templates.TemplateResponse('admin/dynamic_flex_builder.html', ctx(request, db, session, form_error=None, form_values={}, preview_json='', fields=[]))

@router.post('/templates/dynamic-flex-builder')
def dynamic_flex_builder_submit(
    request:Request,
    template_name:str=Form(''),
    approved_query_id:str=Form(''),
    alt_text:str=Form('BK-Moph Notify Flex Message'),
    flex_json:str=Form(''),
    save_as_template:str=Form('0'),
    db:Session=Depends(get_db)
):
    session=require_session(request)
    require_menu(db, session, 'templates')
    from app.repositories.approved_queries import get_by_id as get_query_by_id
    from app.services.hosxp_query import preview_query
    rows = []
    fields = []
    preview_json = ''
    form_values = {
        'template_name': template_name,
        'approved_query_id': approved_query_id,
        'alt_text': alt_text,
        'flex_json': flex_json,
        'save_as_template': save_as_template,
    }
    try:
        if str(approved_query_id or '').strip():
            q = get_query_by_id(db, int(approved_query_id))
            if q:
                data = preview_query(q.sql_text, max_rows=min(q.max_rows or 20, 20))
                rows = enrich_alert_rows(db, data.get('rows') or [], str(request.base_url).rstrip('/'))
        fields = get_available_fields(rows)
        preview_payload = build_dynamic_template_payload('flex_dynamic', flex_json, alt_text, rows)
        preview_json = json.dumps(preview_payload, ensure_ascii=False, indent=2)
        if save_as_template == '1' and (template_name or '').strip():
            create_template(db, template_name.strip(), 'flex_dynamic', flex_json, alt_text.strip() or 'BK-Moph Notify Flex Message')
            write_log(db, session.get('username'), client_ip(request), 'template.create.dynamic_flex', 'success', template_name.strip())
        return templates.TemplateResponse('admin/dynamic_flex_builder.html', ctx(request, db, session, form_error=None, form_values=form_values, preview_json=preview_json, fields=fields))
    except Exception as exc:
        return templates.TemplateResponse('admin/dynamic_flex_builder.html', ctx(request, db, session, form_error=str(exc), form_values=form_values, preview_json=preview_json, fields=fields), status_code=400)


@router.get('/alerts/cases')
def alert_cases_page(request:Request, db:Session=Depends(get_db)):
    session=require_session(request)
    require_menu(db, session, 'notify')
    return templates.TemplateResponse('admin/alert_cases.html', ctx(
        request, db, session,
        alert_cases=get_alert_cases(db)
    ))

@router.get('/alerts/claim')
def alert_claim_page(request:Request, case_key:str, db:Session=Depends(get_db)):
    case = get_alert_case_by_key(db, case_key)
    if not case:
        raise HTTPException(status_code=404, detail='case not found')
    return templates.TemplateResponse('public/claim_case.html', {
        'request': request,
        'case': case,
        'error': None,
        'success': False,
    })

@router.post('/alerts/claim')
def alert_claim_submit(request:Request, case_key:str=Form(...), receiver_name:str=Form(''), db:Session=Depends(get_db)):
    case = get_alert_case_by_key(db, case_key)
    if not case:
        raise HTTPException(status_code=404, detail='case not found')
    if case.status == 'CLAIMED':
        return templates.TemplateResponse('public/claim_case.html', {
            'request': request,
            'case': case,
            'error': 'เคสนี้มีผู้รับเคสแล้ว',
            'success': False,
        })
    session = get_current_session(request)
    receiver = (session.get('username') if session else '') or receiver_name.strip()
    if not receiver:
        return templates.TemplateResponse('public/claim_case.html', {
            'request': request,
            'case': case,
            'error': 'กรุณาระบุชื่อผู้รับเคส',
            'success': False,
        })
    claim_case(db, case, receiver)
    return templates.TemplateResponse('public/claim_case.html', {
        'request': request,
        'case': case,
        'error': None,
        'success': True,
    })

@router.get('/logout')
def logout(request:Request, db:Session=Depends(get_db)):
    session=get_current_session(request)
    if session: write_log(db, session.get('username'), client_ip(request), 'logout', 'success', None)
    destroy_session(request.cookies.get(settings.session_cookie_name))
    response=RedirectResponse('/login', status_code=302)
    response.delete_cookie(settings.session_cookie_name, path='/')
    response.delete_cookie(settings.csrf_cookie_name, path='/')
    return response
