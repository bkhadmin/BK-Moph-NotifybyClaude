# CLAUDE.md — BK-Moph-Notify

## Project Overview

**BK-Moph Notify** — ระบบจัดการและส่ง notification ผ่าน MOPH Notify (กระทรวงสาธารณสุข)
รองรับ lab alert cases, message templating, scheduled notifications, และ multi-provider authentication

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | **FastAPI** 0.115.0 + Uvicorn (ASGI) |
| ORM | **SQLAlchemy** 2.0 + PyMySQL |
| Database | **MySQL 8.0** |
| Cache/Session | **Redis** |
| Templates | **Jinja2** |
| HTTP Client | **HTTPX** (async) |
| Auth | Passlib + Bcrypt, Session cookie, OAuth2, PyJWT |
| Scheduler | Custom cron worker (30-second polling) |
| Deployment | **Docker Compose** (8 containers) |

## Directory Structure

```
BK-Moph-Notify/
├── backend/
│   ├── app/
│   │   ├── api/v1/router.py              # REST API routes (minimal)
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic BaseSettings (89 env vars)
│   │   │   ├── security.py              # Bcrypt password hashing
│   │   │   ├── middleware.py            # AccessLog, CSRF, SecurityHeaders middleware
│   │   │   ├── session.py               # Redis-based session management
│   │   │   └── csrf.py                  # CSRF token generation/validation
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy DeclarativeBase
│   │   │   └── session.py               # Engine & SessionLocal factory
│   │   ├── models/                      # 19 SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── role_permission.py
│   │   │   ├── menu.py
│   │   │   ├── alert_case.py
│   │   │   ├── message_template.py
│   │   │   ├── schedule_job.py
│   │   │   ├── schedule_job_log.py
│   │   │   ├── send_log.py
│   │   │   ├── delivery_status.py
│   │   │   ├── notify_room.py
│   │   │   ├── approved_query.py
│   │   │   ├── media_file.py
│   │   │   ├── access_log.py
│   │   │   ├── ip_ban.py
│   │   │   ├── provider_profile.py
│   │   │   └── provider_profile_history.py
│   │   ├── repositories/                # 18 data access layer modules (CRUD)
│   │   ├── services/                    # 32 business logic modules
│   │   │   ├── send_pipeline.py         # Core send flow
│   │   │   ├── moph_notify.py           # MOPH Notify API client
│   │   │   ├── alert_case_service.py    # Lab alert tracking
│   │   │   ├── hosxp_query.py           # HosXP DB query executor
│   │   │   ├── sql_guard.py             # SQL injection prevention
│   │   │   ├── rbac.py                  # Role-based access control
│   │   │   ├── provider_auth.py         # OAuth2 Health ID / Provider token exchange
│   │   │   ├── sso_service.py           # SSO JWT validation (providerlogin)
│   │   │   ├── scheduler_service.py     # next_run_at computation
│   │   │   ├── job_runner.py            # Single job executor
│   │   │   ├── template_render.py       # Jinja2 template substitution
│   │   │   ├── dynamic_template_renderer.py  # lab_critical_claim / flex_dynamic
│   │   │   ├── flex_builder_service.py  # LINE Flex message builder
│   │   │   ├── flex_template_merger.py  # Merge Flex JSON with data rows
│   │   │   ├── flex_transform.py        # carousel / top5 / full_list
│   │   │   ├── flex_table_renderer.py   # SQL result → Flex table
│   │   │   ├── flex_payload_sanitizer.py  # XSS / structure sanitizer
│   │   │   ├── flex_validator.py        # Flex JSON structure validator
│   │   │   ├── dynamic_flex_fields.py   # Dynamic field expansion
│   │   │   ├── lab_alert_renderer.py    # Lab alert → Flex carousel with claim button
│   │   │   ├── claim_security.py        # HMAC-signed claim URL builder
│   │   │   ├── claim_notify_service.py  # Send notification on claim
│   │   │   ├── claim_url_builder.py     # Claim URL construction
│   │   │   ├── media_service.py         # File upload handling
│   │   │   ├── chart_data.py            # Dashboard statistics
│   │   │   ├── pagination.py            # Query result pagination
│   │   │   ├── csv_export.py            # Export logs to CSV
│   │   │   ├── xlsx_export.py           # Export logs to Excel
│   │   │   ├── template_porter.py       # Template import/export
│   │   │   ├── timezone_utils.py        # Bangkok timezone conversion
│   │   │   └── timezone_write.py        # Write timezone-aware datetimes
│   │   ├── endpoints/
│   │   │   └── web.py                   # Jinja2 web routes (~1500+ lines)
│   │   ├── templates/                   # HTML templates (26 files)
│   │   │   ├── auth/login.html
│   │   │   ├── admin/
│   │   │   └── public/
│   │   ├── static/css/, static/js/
│   │   ├── utils/thai_datetime.py
│   │   ├── worker.py                    # Background retry loop (30s polling)
│   │   ├── worker_scheduler.py          # Scheduled job executor
│   │   ├── beat.py                      # Heartbeat monitor
│   │   └── main.py                      # FastAPI app init
│   ├── scripts/bootstrap.py             # DB schema + seed data (run on startup)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── Dockerfile.scheduler
├── nginx/production.conf
├── database/                            # SQL migration scripts
├── examples/flex_message_templates/
├── docker-compose.prod.yml
├── .env / .env.example
└── CLAUDE.md
```

## Setup & Running

```bash
# Copy env
cp .env.example .env
# แก้ไข .env ให้ครบ (ดู section Environment Variables ด้านล่าง)

# Build + Start (Docker Desktop)
docker compose -f docker-compose.prod.yml up -d --build

# ดู logs
docker compose -f docker-compose.prod.yml logs -f app

# Development (ไม่ใช้ Docker)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Ports:**
- `8012` — Nginx (production entry)
- `8000` — FastAPI (direct/dev)
- `8081` — Adminer (DB admin)

## Docker Compose Services

| Service | Image | หน้าที่ |
|---------|-------|--------|
| nginx | nginx:1.27-alpine | Reverse proxy, static files |
| app | ./backend (build) | FastAPI main app |
| worker | ./backend (build) | Retry failed notifications ทุก 30s |
| beat | ./backend (build) | Heartbeat monitor |
| scheduler | ./backend (build) | Execute scheduled jobs |
| mysql | mysql:8.0 | Main database |
| redis | redis:7-alpine | Session cache |
| adminer | adminer:4 | DB GUI |
| cloudflared | cloudflare/cloudflared | Tunnel (ต้องมี CF_TUNNEL_TOKEN) |

> ถ้าไม่มี CF_TUNNEL_TOKEN ให้ comment `cloudflared` service ออก ก่อน docker compose up

## Environment Variables สำคัญ

```env
# Core
APP_SECRET_KEY=             # session signing key
APP_URL=http://192.168.191.12:8012
NGINX_PORT=8012

# Database
MYSQL_HOST=mysql
MYSQL_DATABASE=bk_moph_notify
MYSQL_USER=bknotify
MYSQL_PASSWORD=
MYSQL_ROOT_PASSWORD=
REDIS_URL=redis://redis:6379/0

# MOPH Notify API
MOPH_NOTIFY_BASE_URL=https://morpromt2f.moph.go.th
MOPH_NOTIFY_CLIENT_KEY=
MOPH_NOTIFY_SECRET_KEY=

# Health ID OAuth2
HEALTH_ID_BASE_URL=https://moph.id.th
HEALTH_ID_CLIENT_ID=
HEALTH_ID_CLIENT_SECRET=
HEALTH_ID_REDIRECT_URI=http://<host>/api/v1/auth/provider/callback

# Provider API
PROVIDER_BASE_URL=https://provider.id.th
PROVIDER_CLIENT_ID=
PROVIDER_SECRET_KEY=

# HosXP DB (read-only)
HOSXP_DB_HOST=
HOSXP_DB_PORT=3306
HOSXP_DB_NAME=hosxp
HOSXP_DB_USER=
HOSXP_DB_PASSWORD=
MAX_QUERY_ROWS=200
MAX_QUERY_SECONDS=20

# SSO จาก providerlogin
SSO_ENABLED=true
SSO_JWT_SECRET=             # ต้องตรงกับ providerlogin JWT_SECRET
SSO_APP_ID=app-moph-notify  # ต้องตรงกับ app_id ใน providerlogin applications table
PROVIDERLOGIN_URL=http://localhost:3000
```

## Database Models (19 ตาราง)

| Model | คำอธิบาย |
|-------|----------|
| User | บัญชีผู้ใช้ — auth_type: local/provider, มี role_id, provider_account_id |
| Role | RBAC roles: superadmin/admin1/admin2/user |
| Permission | Permission definitions (menu.dashboard, notify_rooms, ฯลฯ) |
| RolePermission | Mapping role → permissions |
| Menu | UI menu items |
| AlertCase | Lab critical alert — case_key (SHA256[:40] unique), status: NEW/CLAIMED |
| MessageTemplate | template_type: text/flex/lab_critical_claim/flex_dynamic/flex_full_list/flex_top5 |
| ScheduleJob | schedule_type: once/interval/daily/hourly/monthly/cron, มี next_run_at |
| ScheduleJobLog | ผลการ execute แต่ละ job |
| SendLog | ประวัติส่ง — status: pending/success/failed/retrying, retry_count (max 5) |
| DeliveryStatus | Sub-log of each delivery attempt |
| NotifyRoom | MOPH Notify credentials (client_key/secret_key) หลาย room |
| ApprovedQuery | SQL ที่ whitelist แล้ว พร้อม max_rows |
| MediaFile | ไฟล์ที่ upload ขึ้นมา |
| AccessLog | ทุก action ของ user |
| IpBan | บล็อก IP อัตโนมัติ (threshold/window configurable) |
| ProviderProfile | Cache ข้อมูล provider profile |
| ProviderProfileHistory | Audit การเปลี่ยนแปลง profile |

## Authentication Flow (4 ช่องทาง)

### 1. Local Login
```
POST /auth/login (username, password)
→ bcrypt verify
→ create_session → Redis SET bk_notify_session:{id}
→ Set-Cookie + Redirect /dashboard
```

### 2. Health ID OAuth2
```
GET /auth/provider/redirect
→ Redirect → moph.id.th/oauth/redirect?client_id=...&state=...

GET /auth/provider/callback?code=...&state=...
→ exchange_health_token(code) → access_token
→ exchange_provider_token(health_token)  [ลอง 4 variants]
→ fetch_provider_profile(provider_token)
→ upsert_provider_user(db, profile)
→ create_session → Redirect /dashboard
```

### 3. SSO จาก providerlogin (JWT HS256)
```
GET /auth/sso?sso_token=<jwt>
→ PyJWT.decode(sso_jwt_secret, algorithms=['HS256'], leeway=15s)
→ validate: iss='providerlogin', aud='web-apps', appId=sso_app_id, scope='app-access'
→ extract: sub, providerId, nameTh, username, hcode, hnameTh
→ upsert_provider_user(db, profile)
→ create_session → Redirect /dashboard
```

### 4. Logout
```
GET /auth/logout
→ delete_session(redis) → clear cookie → Redirect /login
```

## RBAC Roles & Permissions

| Role | Level | สิทธิ์ |
|------|-------|--------|
| superadmin | 4 | ทุกอย่าง + RBAC management |
| admin1 | 3 | ทุกอย่างยกเว้น RBAC |
| admin2 | 2 | ส่ง message จำกัด |
| user | 1 | อ่านอย่างเดียว |

**Permission Codes:** menu.dashboard, menu.users, menu.logs, menu.rbac, menu.notify, menu.queries, menu.templates, menu.schedules, menu.media, notify_rooms, claim_notify_settings

## Services หลัก

### Send Pipeline (`send_pipeline.py`)
```
send_with_log(db, username, messages, detail, notify_room_id):
1. Sanitize messages (XSS removal, Flex structure validation)
2. Create SendLog(status='pending')
3. Send via moph_notify.py (retry 3 ครั้ง)
4. Update log status (success/failed)
5. Create DeliveryStatus

retry_failed_log() — Worker เรียกทุก 30s, max retry = 5
```

### MOPH Notify API (`moph_notify.py`)
```
POST {MOPH_NOTIFY_BASE_URL}/api/notify/send
Headers: client-key, secret-key
Body: {"messages": [...]}
Retry: exponential backoff (max 3 attempts)
Credentials: จาก NotifyRoom (override env vars ได้)
```

### Alert Case Workflow (`alert_case_service.py`)
```
build_case_key(row) → SHA256(hn|lab_items_name|result|date|time|dept)[:40]
ensure_case_for_row(db, row) → INSERT หรือ GET AlertCase
enrich_alert_rows(db, rows, base_url) → add case_key, claim_url (HMAC-signed), case_status
filter_rows_for_send(rows) → เอาเฉพาะ status != 'CLAIMED'
mark_rows_sent(db, rows) → increment sent_count, update last_sent_at
```

### SQL Guard (`sql_guard.py`)
- รับเฉพาะ SELECT เท่านั้น
- Block: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, INTO OUTFILE, LOAD_FILE, SLEEP, BENCHMARK
- Remove comments (`/* */`, `--`) ก่อน validate
- Wrap query: `SELECT * FROM ({sql}) _bk_limit LIMIT {max_rows}`

### HosXP Query (`hosxp_query.py`)
```
preview_query(sql_text, max_rows):
1. ensure_safe_select(sql) — sql_guard validation
2. Execute บน HosXP DB (separate connection pool)
3. Timeout: MAX_QUERY_SECONDS (default 20)
4. Return {"columns": [...], "rows": [...], "row_count": n}
```

### Scheduler (`worker_scheduler.py`)
```
execute_job(db, job):
1. Run ApprovedQuery via hosxp_query
2. Build messages (text/flex ตาม template_type)
3. Enrich + filter alert rows (ถ้าเป็น lab_critical)
4. send_with_log(...)
5. mark_rows_sent(...)
6. Create ScheduleJobLog
7. Compute next_run_at, update job

schedule_type → next_run_at:
  once     → parse ISO datetime
  interval → now + interval_minutes
  daily    → tomorrow HH:MM
  hourly   → next hour boundary
  monthly  → +30 days
  cron     → croniter.get_next()
```

### Flex Message Types (`flex_transform.py` + `dynamic_template_renderer.py`)

| template_type | ใช้สำหรับ |
|--------------|----------|
| text | ข้อความธรรมดา |
| flex | Flex JSON custom |
| lab_critical_claim | Lab alert carousel + claim button (HMAC URL) |
| flex_dynamic | Dynamic fields จาก Flex JSON template |
| flex_full_list | Paginated table (8 items/page) |
| flex_top5 | Top 5 ranked dashboard |
| flex_carousel | Carousel bubbles (max 10) |

## Web Endpoints หลัก (`endpoints/web.py`)

| Route | หน้าที่ |
|-------|--------|
| GET / | Redirect → /dashboard |
| GET/POST /auth/login | Local login |
| GET /auth/provider/redirect | OAuth2 redirect |
| GET /auth/provider/callback | OAuth2 callback |
| GET /auth/sso | SSO JWT login |
| GET /dashboard | Summary stats |
| GET/POST /admin/users | User management |
| GET/POST /admin/rbac | Role/permission management |
| GET/POST /admin/templates | Message templates |
| GET/POST /admin/queries | Approved SQL queries |
| POST /admin/queries/{id}/preview | Test query + preview results |
| GET/POST /admin/schedules | Scheduled jobs |
| POST /admin/schedules/{id}/run-now | Manual trigger |
| GET/POST /admin/notify-rooms | MOPH Notify rooms |
| GET /alerts | Lab alert case list |
| GET /alerts/{case_key}/claim | Mark case as claimed |
| GET /admin/logs/access | Access log |
| GET /admin/logs/send | Send log |
| GET /admin/logs/schedule-jobs | Scheduler log |
| GET/POST /admin/media | Media files |

## Background Workers

| Process | Command | หน้าที่ |
|---------|---------|--------|
| worker | `python -m app.worker` | Retry failed SendLogs ทุก 30s |
| worker_scheduler | `python -m app.worker_scheduler` | Execute due ScheduleJobs |
| beat | `python -m app.beat` | Heartbeat monitor |

## Security

- **CSRF** — cookie + header dual token validation
- **Session** — HttpOnly, Secure (prod), SameSite=lax, 12h expiry (Redis)
- **IP Ban** — auto-block หลัง N failures ใน M minutes (configurable)
- **Login rate limit** — max 5 attempts
- **SQL injection** — whitelist + sql_guard (SELECT only)
- **Security headers** — X-Frame-Options, X-Content-Type-Options
- **Flex sanitizer** — remove `<script>`, dangerous event handlers
- **SSO JWT** — HS256, validate iss/aud/appId/scope, leeway 15s

## Bootstrap (`scripts/bootstrap.py`)

รันอัตโนมัติตอน `docker compose up` ก่อน uvicorn:
1. Create all tables (SQLAlchemy `create_all`)
2. Insert default roles: superadmin, admin1, admin2, user
3. Insert default permissions & menus
4. Create role-permission mappings
5. Create default superadmin user (จาก `INTERNAL_SUPERADMIN_*` env)

## SSO Integration กับ providerlogin

### การตั้งค่าใน providerlogin
ต้องมี record ใน `applications` table:
```sql
INSERT INTO applications (app_id, name, icon, url, is_active)
VALUES ('app-moph-notify', 'MOPH Notify', '🔔', 'http://<host>/auth/sso', 1);
```

### การตั้งค่าใน .env
```env
SSO_ENABLED=true
SSO_JWT_SECRET=<ต้องตรงกับ JWT_SECRET ของ providerlogin>
SSO_APP_ID=app-moph-notify
PROVIDERLOGIN_URL=http://localhost:3000
```

### Flow
```
User คลิก MOPH Notify ใน providerlogin dashboard
→ providerlogin สร้าง JWT (HS256, 5min TTL)
→ Redirect → http://<app>/auth/sso?sso_token=<jwt>
→ sso_service.verify_sso_token() validate
→ upsert user → session → dashboard
```

## External API Integrations

| Service | Endpoint | Notes |
|---------|----------|-------|
| MOPH Notify | `POST /api/notify/send` | Headers: client-key, secret-key |
| Health ID | `/api/v1/token` | OAuth2 PKCE flow |
| Provider API | `/api/v1/services/profile` | Token exchange (4 variants) |
| HosXP DB | MySQL read-only | SQL guard enforced, 20s timeout |
