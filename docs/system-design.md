# BK-Moph-Notify — System Design Document
> เวอร์ชันปัจจุบัน ณ เมษายน 2569 (อัปเดตตามระบบที่ใช้งานจริง)

---

## 1. Executive Summary

ระบบ **BK-Moph-Notify** เป็นแพลตฟอร์มสำหรับบริหารจัดการการส่งข้อความแจ้งเตือนผู้ป่วยวิกฤต ผ่านช่องทาง **MOPH Notify** และ **Telegram** โดยมีระบบ "รับเคส" (Claim) เพื่อให้เจ้าหน้าที่ระบุว่าได้รับทราบและดำเนินการกับผู้ป่วยรายนั้นแล้ว

ใช้งานจริงที่ **โรงพยาบาลบางระกำ** สำหรับแจ้งเตือน LAB วิกฤต, ยาวิกฤต (EGFR+Metformin), และผู้ป่วย MDR

---

## 2. สถาปัตยกรรมจริง (As-Built Architecture)

### Stack ที่ใช้จริง

| Component | Technology |
|-----------|-----------|
| Web Framework | FastAPI + Jinja2 (Server-Rendered) |
| Database | MySQL 8.0 |
| Cache / Session | Redis 7 |
| Scheduler | Custom Python loop (`worker_scheduler.py`) |
| Reverse Proxy | Nginx 1.27-alpine |
| Tunnel | Cloudflare Zero Trust Tunnel (`cloudflared`) |
| Container | Docker Compose |
| Auth | SSO via providerlogin (JWT) + TOTP MFA (superadmin) |

> **หมายเหตุ:** ระบบใช้ custom scheduler loop แทน Celery เพื่อความเรียบง่ายในการ deploy

---

## 3. Docker Services

```
services:
  mysql       — ฐานข้อมูลหลัก (MySQL 8.0)
  redis       — session store + state cache (Redis 7)
  app         — FastAPI web app (port 8000 ภายใน)
  worker      — (reserved/unused ปัจจุบัน)
  beat        — (reserved/unused ปัจจุบัน)
  scheduler   — custom Python scheduler loop (worker_scheduler.py)
  nginx       — reverse proxy (port 80 LAN, port 8080 Cloudflare)
  cloudflared — Cloudflare Zero Trust Tunnel
  adminer     — DB admin UI (port 8080 ภายใน, LAN only)
```

### Deploy Command
```bash
cd /root/BK-Moph-NotifybyClaude
git pull
docker compose -f docker-compose.prod.yml up -d --build app scheduler
docker compose -f docker-compose.prod.yml restart nginx
```

> ⚠️ ต้อง `--build` ทุกครั้ง (ไม่มี volume mount สำหรับ code)  
> ⚠️ ต้อง restart nginx หลัง rebuild app เสมอ (nginx cache IP เก่าของ container)

---

## 4. Network & Access

| เส้นทาง | URL | หมายเหตุ |
|---------|-----|----------|
| LAN Admin | `http://192.168.191.12:8012` | เข้าได้ทุก path |
| Public (Cloudflare) | `https://alertmoph.bkhospital.go.th` | จำกัด path: `/alerts/claim`, `/line/` |
| Adminer | `http://192.168.191.12:8080` | LAN only |

### Cloudflare Tunnel Public Hostnames
- Rule 1: `alertmoph.bkhospital.go.th` path `/alerts/claim` → `http://nginx:8080`
- Rule 2: `alertmoph.bkhospital.go.th` path `/line/` → `http://nginx:8080`

---

## 5. Authentication Flow

### 5.1 SSO Login (ปกติ)
```
User → /login → SSO redirect → providerlogin JWT
     → /auth/sso?sso_token=<JWT> → verify → session → /dashboard
```

### 5.2 Local Login (Fallback)
```
User → /login → username/password → session → /dashboard
```

### 5.3 MFA (Superadmin เท่านั้น)
```
Login success → detect superadmin → Redis temp session (5 min)
→ /login/mfa (ถ้ามี secret) หรือ /login/mfa/setup (ครั้งแรก)
→ TOTP verify (pyotp) → session จริง → /dashboard
```

### 5.4 LINE Login (Claim Page)
```
User กด claim link → /alerts/claim → ไม่มี LINE cookie
→ กด "Login with LINE" → /line/login → LINE OAuth
→ /line/callback → บันทึก line_users → set cookie 90 วัน
→ redirect กลับ claim page (พร้อม pre-fill ชื่อ)
```

---

## 6. Role & Menu Permission

### Roles
| Role | คำอธิบาย |
|------|----------|
| `superadmin` | สิทธิ์ทุกอย่าง + MFA required |
| `admin` | บริหารจัดการทั่วไป |
| `user` | ใช้งานตามเมนูที่ได้รับ |

### Menu Codes (RBAC)
| Menu Code | หน้าที่ |
|-----------|--------|
| `dashboard` | หน้าหลัก |
| `users` | จัดการผู้ใช้ |
| `queries` | SQL Query |
| `templates` | Message Templates |
| `media` | อัปโหลดรูปภาพ |
| `notify_rooms` | ห้อง MOPH Notify / Telegram |
| `notify` | ส่งข้อความ / ทดสอบ |
| `schedules` | ตั้งเวลาส่งอัตโนมัติ |
| `logs` | ดู Logs ต่างๆ |
| `rbac` | จัดการสิทธิ์ (superadmin) |
| `alert_type_configs` | ตั้งค่า Alert Type |
| `claim_notify_settings` | ตั้งค่าข้อความตอบกลับหลังรับเคส |

---

## 7. Alert & Claim System

### 7.1 Flow การแจ้งเตือน
```
HOSxP DB (read-only) → Scheduler ทุก 5 นาที
→ Query ดึงข้อมูลผู้ป่วยวิกฤต
→ Dedup ด้วย case_key (SHA256 hash) หรือ lab_order_number
→ สร้าง alert_case (status=NEW)
→ Build Flex Message → ส่งผ่าน MOPH Notify หรือ Telegram
→ แต่ละ bubble มี "รับเคส" button (signed URL อายุ 1 ชั่วโมง)
```

### 7.2 Claim Flow
```
เจ้าหน้าที่กด "รับเคส" link → /alerts/claim?case_key=...&expires=...&sig=...
→ ตรวจ HMAC signature + expiry
→ แสดงหน้าขอชื่อผู้รับเคส (LINE pre-fill หรือ manual input)
→ POST /alerts/claim → update alert_cases (status=CLAIMED, claimed_by, claimed_at)
→ ส่ง claim notify กลับห้องเดิมที่ alert ครั้งแรก
```

### 7.3 Alertroom (Auto Room Routing)
```
Query มี field "alertroom" (เช่น "061,062")
→ Schedule ตั้งเป็น "ห้องอัตโนมัติ (alertroom)"
→ ระบบ parse codes → หา notify_rooms ที่ room_code ตรงกัน
→ ส่งไปทุกห้องที่พบ
→ ถ้าไม่พบห้อง → fallback ไป default room (.env)
```

### 7.4 Alert Types ที่ใช้งาน
| Type Code | คำอธิบาย |
|-----------|---------|
| `lab_critical` | LAB วิกฤต (ค่าผิดปกติ) |
| `drug_critical_egfr` | ยา Metformin + EGFR ต่ำ |
| `mdr_critical` | ผู้ป่วย MDR / เชื้อดื้อยา |

---

## 8. Notify Channels

| Channel Type | ใช้งาน | client_key | secret_key |
|-------------|--------|-----------|-----------|
| `moph_notify` | MOPH Notify API | Client Key | Secret Key |
| `telegram` | Telegram Bot | Bot Token | Chat ID |

**MOPH Notify:** POST `/api/notify/send` พร้อม client-key, secret-key ใน header  
**Telegram:** POST `https://api.telegram.org/bot{token}/sendMessage` — Flex JSON แปลงเป็น plain text

---

## 9. Database Schema (ตารางหลัก)

| ตาราง | คำอธิบาย |
|-------|---------|
| `users` | ผู้ใช้งานระบบ (id, username, display_name, role_id, totp_secret) |
| `roles` | บทบาท (superadmin, admin, user) |
| `menus` | รายการเมนูในระบบ |
| `role_menus` | สิทธิ์เมนูตาม role |
| `notify_rooms` | ห้อง MOPH Notify / Telegram (room_code, channel_type) |
| `approved_queries` | SQL query ที่ผ่านการอนุมัติ |
| `message_templates` | template ข้อความ (text/flex/claim_alert) |
| `schedule_jobs` | งานที่ตั้งเวลา (use_alertroom, notify_room_id) |
| `schedule_job_logs` | log การรัน scheduler |
| `send_logs` | log การส่งข้อความ |
| `delivery_statuses` | สถานะ delivery แต่ละครั้ง |
| `alert_cases` | เคสที่แจ้งเตือน (case_key, status, claimed_by) |
| `alert_type_configs` | ตั้งค่า alert type (key_fields, field_map, display_lines) |
| `line_users` | ผูก LINE userId กับชื่อจริง |
| `access_logs` | log การเข้าถึงระบบ |

---

## 10. Scheduler Design

**ไฟล์หลัก:** `backend/app/worker_scheduler.py`

```
run_once() → get_due_jobs() → execute_job(job) ทุกงานที่ถึงเวลา
```

**Schedule Types:**
- `interval` — ทุก X นาที
- `daily` — รายวัน เวลาที่กำหนด (HH:MM)
- `once` — ครั้งเดียว แล้ว deactivate
- `cron` — cron expression

**Poll interval:** 5 วินาที

---

## 11. Security

| ชั้น | มาตรการ |
|-----|--------|
| Auth | SSO JWT + TOTP MFA (superadmin) |
| Session | Redis session, httponly cookie |
| Claim URL | HMAC-SHA256 signed, expiry 1 ชั่วโมง |
| LINE Login | OAuth 2.0, state CSRF (Redis 5 นาที), cookie httponly 90 วัน |
| SQL | SELECT only, keyword guard, max_rows limit |
| Headers | X-Frame-Options: DENY, X-Content-Type-Options: nosniff |
| IP | Cloudflare path restriction (public) |

---

## 12. Key Files

```
backend/
├── app/
│   ├── main.py                    — startup, middleware, auto-migration
│   ├── core/config.py             — settings (.env)
│   ├── endpoints/web.py           — routes ทั้งหมด (~2100 บรรทัด)
│   ├── models/                    — SQLAlchemy models
│   ├── repositories/              — DB access layer
│   ├── services/
│   │   ├── job_runner.py          — dead code (ไม่ถูกใช้)
│   │   ├── alert_case_service.py  — dedup, enrich, mark_sent
│   │   ├── send_pipeline.py       — route moph_notify/telegram
│   │   ├── moph_notify.py         — MOPH Notify API client
│   │   ├── telegram_notify.py     — Telegram Bot client
│   │   ├── line_login.py          — LINE OAuth 2.0
│   │   └── hosxp_query.py         — HOSxP DB query
│   └── templates/
│       ├── admin/                 — หน้า admin ทั้งหมด
│       └── public/                — claim_case.html, line_set_name.html
├── worker_scheduler.py            — scheduler loop หลัก
└── scripts/bootstrap.py           — สร้างตารางและ seed data
```

---

## 13. Auto-Migration

ระบบทำ schema migration อัตโนมัติที่ startup ใน `main.py`:
- `notify_rooms.channel_type` — moph_notify | telegram
- `notify_rooms.secret_key` — nullable
- `line_users` table
- `schedule_jobs.use_alertroom`
- `alert_cases.item_name` — TEXT (รองรับ plain_text ยาว)
