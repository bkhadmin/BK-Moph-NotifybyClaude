# BK-Moph Notify

ระบบแจ้งเตือนผ่าน LINE สำหรับโรงพยาบาล รองรับการแจ้งเตือนค่าผลแล็บวิกฤต (LAB Critical) และยาวิกฤต (Drug Critical) พร้อมระบบ "รับเคส" เพื่อยืนยันการรับทราบ

---

## สถาปัตยกรรม

```
nginx (reverse proxy)
  └── app       (FastAPI + Jinja2 — web UI + API)
  └── scheduler (ดึงข้อมูลจาก HosXP + ส่ง LINE)
  └── worker    (Celery worker)
  └── beat      (Celery beat)
  └── mysql     (ฐานข้อมูลระบบ)
  └── redis     (message broker)
  └── cloudflared (optional — Cloudflare Tunnel)
```

---

## ความต้องการระบบ

- Docker + Docker Compose
- เครื่อง Server Linux (แนะนำ Ubuntu 22.04+)
- เชื่อมต่อฐานข้อมูล HosXP ได้ (MySQL read-only)
- API Key จาก MOPH Notify ([https://morpromt2f.moph.go.th](https://morpromt2f.moph.go.th))

---

## ขั้นตอนติดตั้ง

### 1. Clone โปรเจกต์

```bash
git clone https://github.com/bkhadmin/BK-Moph-NotifybyClaude.git
cd BK-Moph-NotifybyClaude
```

### 2. สร้างไฟล์ `.env`

```bash
cp .env.example .env
```

แก้ไข `.env` ตามสภาพแวดล้อมจริง:

| ตัวแปร | คำอธิบาย | ตัวอย่าง |
|---|---|---|
| `APP_URL` | URL ของระบบ | `http://192.168.1.10:8012` |
| `APP_SECRET_KEY` | Secret key สำหรับ session | สุ่มให้ยาว 32+ ตัวอักษร |
| `NGINX_PORT` | Port ที่เปิดบน host | `8012` |
| `MYSQL_DATABASE` | ชื่อ database ระบบ | `bk_moph_notify` |
| `MYSQL_USER` | MySQL user | `bknotify` |
| `MYSQL_PASSWORD` | MySQL password | ตั้งเอง |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | ตั้งเอง |
| `HOSXP_DB_HOST` | IP ของ HosXP DB | `192.168.1.111` |
| `HOSXP_DB_USER` | MySQL user สำหรับ HosXP (read-only) | `readonly_user` |
| `HOSXP_DB_PASSWORD` | Password HosXP DB | — |
| `MOPH_NOTIFY_CLIENT_KEY` | Client Key จาก MOPH Notify | — |
| `MOPH_NOTIFY_SECRET_KEY` | Secret Key จาก MOPH Notify | — |
| `PUBLIC_BASE_URL` | URL สาธารณะสำหรับลิงก์รับเคส | `https://alert.example.go.th` |
| `CLAIM_SIGNING_SECRET` | Secret สำหรับ sign URL รับเคส | สุ่มให้ยาว 32+ ตัวอักษร |

> **หมายเหตุ:** ไม่ต้องใช้ Cloudflare Tunnel ก็ได้ — ลบ service `cloudflared` ออกจาก compose หรือปล่อย `CF_TUNNEL_TOKEN` ว่างไว้

### 3. รันระบบ

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

รอประมาณ 1-2 นาทีให้ container พร้อมทั้งหมด ตรวจสถานะด้วย:

```bash
docker compose -f docker-compose.prod.yml ps
```

ทุก service ควรแสดงสถานะ `healthy` หรือ `running`

### 4. เข้าใช้งาน

เปิดเบราว์เซอร์ไปที่ `http://<IP>:<NGINX_PORT>`

**บัญชีเริ่มต้น (Superadmin):**
- Username: ค่าจาก `INTERNAL_SUPERADMIN_USERNAME` ใน `.env` (default: `superadmin`)
- Password: ค่าจาก `INTERNAL_SUPERADMIN_PASSWORD` ใน `.env`

---

## ตั้งค่าเริ่มต้นหลังติดตั้ง

### 1. เพิ่ม Notify Room

ไปที่ **Notify Rooms** → เพิ่มห้อง LINE พร้อม Client Key / Secret Key

### 2. สร้าง Alert Type Config

ไปที่ **Alert Type Configs** → กด **Seed Default** เพื่อสร้าง `lab_critical` อัตโนมัติ
จากนั้นสร้าง `drug_critical` เพิ่มเองตาม field ของ HosXP

### 3. เพิ่ม Approved Query

ไปที่ **Approved Queries** → เขียน SQL สำหรับดึงข้อมูล LAB/ยาวิกฤตจาก HosXP

### 4. ตั้งค่า Schedule

ไปที่ **Schedules** → กำหนด cron หรือ interval สำหรับ job ส่งแจ้งเตือน

---

## คำสั่งที่ใช้บ่อย

```bash
# ดู log แบบ realtime
docker compose -f docker-compose.prod.yml logs -f app
docker compose -f docker-compose.prod.yml logs -f scheduler

# restart เฉพาะ service
docker compose -f docker-compose.prod.yml restart app
docker compose -f docker-compose.prod.yml restart scheduler

# หยุดทั้งหมด
docker compose -f docker-compose.prod.yml down

# อัปเดตโค้ด
git pull
docker compose -f docker-compose.prod.yml up -d --build app scheduler worker beat
```

---

## เข้าถึงฐานข้อมูล

Adminer (web UI สำหรับ MySQL) เปิดอยู่ที่:

```
http://<IP>:<ADMINER_PORT>
```
(default port: `8081`)

---

## โครงสร้างไฟล์สำคัญ

```
backend/
  app/
    endpoints/web.py          # Routes ทั้งหมด
    models/                   # SQLAlchemy models
    repositories/             # Database access layer
    services/                 # Business logic
      lab_alert_renderer.py   # สร้าง LINE Flex bubble
      claim_notify_service.py # ส่งข้อความหลังรับเคส
    templates/admin/          # Jinja2 templates
    static/                   # CSS, JS, images
  scripts/
    bootstrap.py              # Migration + seed ตอน startup
nginx/
  production.conf             # Nginx config
.env.example                  # ตัวอย่าง environment variables
docker-compose.prod.yml       # Docker Compose สำหรับ production
```

---

## SSO (ไม่บังคับ)

ระบบรองรับ SSO ผ่าน **ProviderLogin** และ **MOPH ID (Health ID)**
ตั้งค่าได้ใน `.env` หัวข้อ `SSO_*` และ `HEALTH_ID_*`
หากไม่ใช้ SSO ให้ตั้ง `SSO_ENABLED=false` และ `PROVIDER_LOGIN_ENABLED=false`

---

## License

ระบบนี้พัฒนาสำหรับใช้งานภายในโรงพยาบาลบางระกำ
