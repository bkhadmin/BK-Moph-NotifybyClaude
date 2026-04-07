# คู่มือการใช้งาน BK-Moph-Notify
> ฉบับละเอียดทุกเมนู — เมษายน 2569

---

## การเข้าสู่ระบบ

### วิธีที่ 1: SSO (Login กลาง)
1. เปิด `http://192.168.191.12:8012`
2. กด **"เข้าสู่ระบบด้วย Provider ID"**
3. ระบบ redirect ไป providerlogin → กรอก Username/Password
4. ระบบดึงข้อมูลและสร้าง session อัตโนมัติ

### วิธีที่ 2: Local Login
1. กรอก Username และ Password ในช่องที่หน้า login
2. กด **"เข้าสู่ระบบ"**

### MFA (เฉพาะ Superadmin)
- ครั้งแรก: ระบบพาไปหน้า Setup MFA → สแกน QR Code ด้วย Google Authenticator
- ครั้งถัดไป: กรอกรหัส 6 หลักจาก Authenticator app

---

## เมนู Dashboard

**URL:** `/dashboard`  
**สิทธิ์:** ทุก role

### แสดงข้อมูล
- **สถิติ Alert Cases วันนี้:** จำนวน NEW / CLAIMED / รวม
- **Send Logs ล่าสุด:** 10 รายการล่าสุดที่ส่งข้อความ
- **Schedule Jobs:** งานที่ Active ทั้งหมด พร้อม next_run_at

---

## เมนู Users (จัดการผู้ใช้)

**URL:** `/users`  
**สิทธิ์:** `users`

### ดูรายการผู้ใช้
- แสดงตาราง: username, display_name, role, last_login
- กด **"แก้ไข"** เพื่อเปลี่ยน role หรือ reset password

### สร้างผู้ใช้ใหม่
1. กด **"+ เพิ่มผู้ใช้"**
2. กรอก username, display_name, password, เลือก role
3. กด **"บันทึก"**

### แก้ไขผู้ใช้
- เปลี่ยน role: เลือก role ใหม่ → บันทึก
- เปลี่ยน password: กรอก password ใหม่ (เว้นว่างถ้าไม่ต้องการเปลี่ยน)
- ลบผู้ใช้: กด **"ลบ"** → ยืนยัน

### Map CID กับตาราง person
- แต่ละ user สามารถ map กับ CID (รหัสประชาชน) ในตาราง `person` ของ HIS ได้
- ใช้สำหรับดึงชื่อผู้ใช้จากฐานข้อมูลผู้ป่วย

---

## เมนู Profiles (ข้อมูลจาก SSO)

**URL:** `/profiles`  
**สิทธิ์:** `users`

- แสดงข้อมูล Provider Profile ของแต่ละ user ที่ login ด้วย SSO
- กด **"ดูรายละเอียด"** เพื่อดู raw profile JSON
- กด **"Sync"** เพื่ออัปเดตข้อมูลจาก Provider ล่าสุด
- Export รายชื่อทั้งหมดเป็น CSV

---

## เมนู Queries (SQL Query)

**URL:** `/queries`  
**สิทธิ์:** `queries`

### ระบบ Query
- เชื่อมต่อฐานข้อมูล HOSxP แบบ **read-only**
- รองรับเฉพาะ `SELECT` statement
- มี keyword guard: ห้าม INSERT, UPDATE, DELETE, DROP, ALTER ฯลฯ

### สร้าง Query ใหม่
1. กด **"+ New Query"**
2. กรอกชื่อ query
3. เขียน SQL ใน editor (รองรับ syntax highlight)
4. กำหนด `max_rows` (จำนวนแถวสูงสุด)
5. กด **"Preview"** เพื่อทดสอบ (แสดงผล 100 แถวแรก)
6. กด **"บันทึก"**

### ทดสอบ Query
- กด **"Run"** เพื่อดูผลลัพธ์จริงจาก HOSxP
- แสดงตาราง + จำนวนแถว + เวลาที่ใช้

### Test Connection
- กด **"Test Connection"** เพื่อตรวจสอบการเชื่อมต่อ HOSxP DB

### ตัวอย่าง Query สำหรับ Alertroom
```sql
SELECT
  hn, vn, ptname, plain_text,
  report_date, report_time,
  main_dep AS alertroom,          -- field นี้ใช้กำหนดห้องส่ง
  main_department
FROM mdr_alert_view
WHERE DATE(report_date) = CURDATE()
```

---

## เมนู Templates (Message Templates)

**URL:** `/templates`  
**สิทธิ์:** `templates`

### ประเภท Template

| Type | คำอธิบาย |
|------|---------|
| `text` | ข้อความธรรมดา แทรกตัวแปรด้วย `{field_name}` |
| `flex` | LINE Flex Message JSON |
| `lab_critical_claim` | Flex พิเศษสำหรับ LAB วิกฤต มีปุ่มรับเคส |
| `claim_alert` | Flex กำหนดเองสำหรับ alert ที่มีระบบรับเคส |
| `flex_full_list` | แสดงทุก row เป็น carousel |
| `dynamic_full_list` | Dynamic template จาก query ทุก row |

### สร้าง Template ใหม่
1. กด **"+ New Template"**
2. กรอกชื่อ, เลือก type
3. กรอก content (ข้อความ หรือ JSON สำหรับ flex)
4. กรอก `alt_text` (ข้อความแสดงใน notification)
5. กด **"บันทึก"**

### การใช้ตัวแปรใน Text Template
```
ผู้ป่วย: {ptname}
HN: {hn}
ค่าผล: {lab_order_result}
แผนก: {cur_dep}
```

### Clone Template
- กด **"Clone"** เพื่อคัดลอก template มาแก้ไข

### Export / Import
- **Export:** ดาวน์โหลด template เป็น JSON
- **Import:** อัปโหลดไฟล์ JSON เพื่อนำเข้า template

---

## เมนู Lab Critical Builder

**URL:** `/templates/lab-critical-builder`  
**สิทธิ์:** `templates`

เครื่องมือสร้าง Flex Message สำหรับ LAB วิกฤตแบบ visual:
- กำหนดสีหัว bubble (`bubble_title_color`)
- กำหนดบรรทัดแสดงผล (`display_lines`)
- Preview แบบ real-time
- บันทึกเป็น template type `lab_critical_claim`

---

## เมนู Claim Alert Builder

**URL:** `/templates/claim-alert-builder`  
**สิทธิ์:** `templates`

เครื่องมือสร้าง Flex Message สำหรับ alert ทั่วไปที่มีปุ่มรับเคส:
- เลือก Alert Type Config
- กำหนด display fields
- Preview ด้วยข้อมูลตัวอย่าง
- บันทึกเป็น template type `claim_alert`

---

## เมนู Dynamic Flex Builder

**URL:** `/templates/dynamic-flex-builder`  
**สิทธิ่:** `templates`

สร้าง Flex Message แบบ dynamic ที่ render ต่าง row ต่างกัน:
- เลือก query
- กำหนด field mapping
- Preview carousel จากข้อมูลจริง

---

## เมนู Media (รูปภาพ)

**URL:** `/media`  
**สิทธิ์:** `media`

- อัปโหลดรูปภาพเพื่อใช้ใน Flex Message
- รองรับ: JPG, PNG, GIF
- ระบบเก็บใน `/app/uploads/`
- Copy URL เพื่อใช้ใน template

---

## เมนู Notify Rooms (ห้องแจ้งเตือน)

**URL:** `/notify/rooms`  
**สิทธิ์:** `notify_rooms`

### ประเภทห้อง

#### MOPH Notify
| Field | คำอธิบาย |
|-------|---------|
| Name | ชื่อห้อง (แสดงใน UI) |
| Room Code | รหัสห้อง เช่น `061`, `HC11252` (ใช้กับ alertroom) |
| Channel Type | `moph_notify` |
| Client Key | Client Key จาก MOPH Notify |
| Secret Key | Secret Key จาก MOPH Notify |

#### Telegram
| Field | คำอธิบาย |
|-------|---------|
| Name | ชื่อห้อง |
| Room Code | รหัสห้อง (ใช้กับ alertroom) |
| Channel Type | `telegram` |
| Client Key | **Bot Token** (`123456:ABC-DEF...`) |
| Secret Key | **Chat ID** (`-100123456789`) |

### สร้างห้องใหม่
1. กด **"+ เพิ่มห้อง"**
2. กรอกข้อมูลตามประเภท channel
3. กด **"บันทึก"**

> **room_code** สำคัญมาก — ต้องตรงกับค่า `alertroom` ใน query เพื่อให้ auto-routing ทำงานได้

---

## เมนู Notify Test (ทดสอบส่งข้อความ)

**URL:** `/notify/test`  
**สิทธิ์:** `notify`

### ทดสอบส่ง Text
1. เลือก Notify Room
2. กรอกข้อความ
3. กด **"ส่งทดสอบ"**

### ทดสอบส่ง Flex
1. วาง Flex JSON ในช่อง editor
2. เลือก Notify Room
3. กด **"Preview"** เพื่อดูตัวอย่าง
4. กด **"ส่ง"**

---

## เมนู Send (ส่งข้อความจาก Template + Query)

**URL:** `/notify/preview` และ `/notify/send-from-template`  
**สิทธิ์:** `notify`

1. เลือก **Approved Query**
2. เลือก **Message Template**
3. เลือก **Notify Room** (หรือ Default)
4. กด **"Preview"** เพื่อดูตัวอย่างก่อนส่ง
5. กด **"ส่งจริง"** เพื่อส่งข้อความ

---

## เมนู Schedules (ตั้งเวลาส่งอัตโนมัติ)

**URL:** `/schedules`  
**สิทธิ์:** `schedules`

### สร้าง Schedule ใหม่
1. กด **"+ New Schedule"**
2. กรอก **Name** (ชื่องาน)
3. เลือก **Schedule Type:**
   - `ทุก X นาที` — interval (ระบุจำนวนนาที)
   - `รายวัน` — daily (ระบุเวลา HH:MM)
   - `ครั้งเดียว` — once
   - `cron` — cron expression
4. เลือก **Approved Query**
5. เลือก **Notify Room:**
   - เลือกห้องคงที่ หรือ
   - เลือก **"📡 ห้องอัตโนมัติ (alertroom)"** — ระบบจะอ่าน field `alertroom` จาก query แล้วส่งไปห้องที่ room_code ตรงกัน
6. เลือก **Message Template**
7. ตั้ง **Status** (Active/Inactive)
8. กด **"บันทึก"**

### ห้องอัตโนมัติ (Alertroom)
- Query ต้องมี column ชื่อ `alertroom` ที่มีค่าเป็น room_code
- รองรับหลายห้อง คั่นด้วย comma: `"061,062"`
- ถ้า room_code ไม่พบในระบบ → fallback ไป default room (.env)

### การจัดการ Schedule
- **Run Now:** กด ▶ เพื่อรันทันที (ไม่รอเวลา)
- **Pause:** ปิด Active → งานหยุดชั่วคราว
- **Delete:** ลบงาน

---

## เมนู Scheduler Monitor

**URL:** `/scheduler-monitor`  
**สิทธิ์:** `schedules`

แสดง log การรัน scheduler ทุกครั้ง:
- วันเวลาที่รัน
- สถานะ: `success` / `failed` / `no_data`
- จำนวน rows ที่ได้
- Error message (ถ้ามี)
- กด **"ดู Log"** เพื่อดูรายละเอียด

---

## เมนู Alert Cases (เคสแจ้งเตือน)

**URL:** `/alerts/cases`  
**สิทธิ์:** ทุก role ที่ login แล้ว (ผ่าน require_session)

### ดูรายการ Alert Cases
- Filter: วันที่, Alert Type, สถานะ (NEW/CLAIMED)
- Default: แสดงเฉพาะวันนี้
- กด **🔍** เพื่อดู source_row_json (ข้อมูลครบทุก field)

### สรุปรายงาน
- Progress bar แสดง claim rate ต่อ item_name
- Export เป็น CSV หรือ Excel

### Manual Claim
1. ไปที่ **Alert Cases** → กด **"Manual Claim"**
2. เลือกเคสที่ต้องการ
3. ระบบสร้าง signed claim URL ให้อัตโนมัติ
4. กด link → กรอกชื่อผู้รับเคส → ยืนยัน

### แก้ไข / ลบเคส
- กด **"แก้ไข"** เพื่อเปลี่ยน status หรือข้อมูลเคส
- กด **"ลบ"** เพื่อลบเคสออก (เคสจะถูกส่งใหม่ในรอบถัดไป)

---

## เมนู Alert Type Configs

**URL:** `/alert-type-configs`  
**สิทธิ์:** `alert_type_configs`

กำหนดค่าสำหรับแต่ละ alert type:

| Field | คำอธิบาย |
|-------|---------|
| Type Code | รหัส เช่น `lab_critical`, `mdr_critical` |
| Display Name | ชื่อแสดงใน UI |
| Bubble Title | หัวข้อ bubble |
| Bubble Title Color | สีหัวข้อ (hex) |
| Required Fields | field ที่ต้องมีในแต่ละ row (JSON array) |
| Key Fields | field ที่ใช้ dedup (SHA256 hash) |
| Field Map | mapping standard_name → column ใน query |
| Display Lines | บรรทัดที่แสดงใน bubble (JSON array) |
| Claim Notify Type | `text` หรือ `flex` |
| Claim Notify Template | template ข้อความตอบกลับหลังรับเคส |

### ตัวแปรที่ใช้ใน Claim Notify Template
```
{patient_name}  — ชื่อผู้ป่วย
{patient_hn}    — HN
{item_name}     — ชื่อรายการ (lab/ยา)
{item_value}    — ค่าผล
{department}    — แผนก
{claimed_by}    — ชื่อผู้รับเคส
{claimed_at}    — เวลาที่รับเคส
{alert_type}    — ประเภท alert
```

---

## เมนู Claim Notify Settings

**URL:** `/settings/claim-notify`  
**สิทธิ์:** `claim_notify_settings`

- ตั้งค่า template ข้อความที่ส่งกลับห้องหลังจากมีคนรับเคส
- แต่ละ Alert Type Config สามารถมี template แยกกันได้
- รองรับทั้ง text และ Flex JSON

---

## เมนู Logs (Access Logs)

**URL:** `/logs/access`  
**สิทธิ์:** `logs`

แสดง access log ทุก request:
- วันเวลา, IP, username, path, method, status code
- Filter ตามวันที่, username, path
- Export เป็น CSV หรือ Excel

---

## เมนู Reports

**URL:** `/reports`  
**สิทธิ์:** `logs`

- สรุปสถิติการส่งข้อความ
- Claim rate แยกตาม alert type
- กราฟแนวโน้มการแจ้งเตือน

---

## เมนู System Connections

**URL:** `/system/connections`  
**สิทธิ์:** superadmin

ตั้งค่าการเชื่อมต่อระบบภายนอก:
- **HOSxP DB:** host, port, database, username, password
- **MOPH Notify:** base URL, default client key, default secret key
- **SSO:** Provider URL, Client ID

---

## เมนู RBAC (จัดการสิทธิ์)

**URL:** `/rbac`  
**สิทธิ์:** `rbac` (superadmin เท่านั้น)

### จัดการ Role และ Menu Permission
1. เลือก Role ที่ต้องการแก้ไข
2. เลือก/ยกเลิก เมนูที่ให้สิทธิ์
3. กด **"บันทึก"**

### Menu Codes
| Code | หน้าจอ |
|------|-------|
| dashboard | Dashboard |
| users | จัดการผู้ใช้ |
| queries | SQL Queries |
| templates | Message Templates |
| media | Media Files |
| notify_rooms | Notify Rooms |
| notify | ส่งข้อความ |
| schedules | Schedules |
| logs | Access Logs |
| rbac | RBAC (superadmin เท่านั้น) |
| alert_type_configs | Alert Type Configs |
| claim_notify_settings | Claim Notify Settings |

---

## หน้า Claim (สาธารณะ)

**URL:** `https://alertmoph.bkhospital.go.th/alerts/claim?case_key=...&expires=...&sig=...&room_id=...`

หน้านี้เปิดสาธารณะผ่าน Cloudflare (ไม่ต้อง login ระบบ)

### 3 สถานะ
1. **มี LINE Login + มีชื่อจริงแล้ว** → ชื่อถูก pre-fill อัตโนมัติ → กดยืนยันครั้งเดียว
2. **มี LINE Login แต่ยังไม่ได้กรอกชื่อ** → แสดงฟอร์มกรอกชื่อจริง
3. **ยังไม่ได้ Login LINE** → แสดงปุ่ม "Login with LINE" + ช่องกรอกชื่อเองแบบ manual

### LINE Login
1. กด **"Login with LINE"**
2. ระบบ redirect ไป LINE OAuth
3. อนุญาต → redirect กลับมา claim page
4. กรอกชื่อจริง-นามสกุล (ครั้งแรกเท่านั้น)
5. ระบบจำ LINE UID ไว้ใน cookie 90 วัน

### ขั้นตอนรับเคส
1. ตรวจสอบข้อมูลผู้ป่วย
2. กรอก/ยืนยันชื่อผู้รับเคส
3. กด **"ยืนยันรับเคส"**
4. ระบบส่งข้อความแจ้งกลับห้อง LINE เดิม

---

## System Settings (.env หลัก)

```env
# App
APP_BASE_URL=http://192.168.191.12:8012
PUBLIC_BASE_URL=https://alertmoph.bkhospital.go.th
SECRET_KEY=<random 64 chars>

# Database
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=bk_moph_notify
MYSQL_USER=bknotify
MYSQL_PASSWORD=<password>
MYSQL_ROOT_PASSWORD=<root_password>

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=<password>

# MOPH Notify (default room)
MOPH_NOTIFY_BASE_URL=https://morpromt2f.moph.go.th
MOPH_NOTIFY_CLIENT_KEY=<client_key>
MOPH_NOTIFY_SECRET_KEY=<secret_key>

# HOSxP
HOSXP_HOST=<hosxp_server_ip>
HOSXP_PORT=3306
HOSXP_DATABASE=hosxp_pcu
HOSXP_USER=<readonly_user>
HOSXP_PASSWORD=<password>

# SSO
SSO_BASE_URL=http://192.168.191.12:3000
SSO_APP_ID=app-moph-notify
SSO_APP_SECRET=<secret>

# LINE Login
LINE_LOGIN_CHANNEL_ID=2009687033
LINE_LOGIN_CHANNEL_SECRET=<secret>
LINE_LOGIN_REDIRECT_URI=https://alertmoph.bkhospital.go.th/line/callback

# Claim Security
CLAIM_SECRET_KEY=<random key>
CLAIM_LINK_EXPIRES_HOURS=1

# Cloudflare
CLOUDFLARED_TOKEN=<token>
```

---

## การ Troubleshoot บ่อย

### 502 Bad Gateway (หลัง rebuild)
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

### MDR Alert failed ทุก 5 นาที
- ตรวจ `item_name` column: `SHOW COLUMNS FROM alert_cases LIKE 'item_name'`
- ต้องเป็น `TEXT` ไม่ใช่ `VARCHAR(255)`
- ถ้าไม่ใช่: `ALTER TABLE alert_cases MODIFY COLUMN item_name TEXT`

### LINE Login กด แล้วขึ้น Bad Request
- ตรวจ LINE Developers Console → Callback URL ต้องเป็น `https://alertmoph.bkhospital.go.th/line/callback`
- ตรวจ `.env` → `LINE_LOGIN_REDIRECT_URI` ต้องตรงกัน
- restart app: `docker compose -f docker-compose.prod.yml up -d --build app`

### Alertroom ส่งไปห้องหลักแทน
- ตรวจ `room_code` ใน notify_rooms ว่าตรงกับค่า `alertroom` ใน query ไหม
- ตรวจ `use_alertroom` ใน schedule_jobs: `SELECT use_alertroom FROM schedule_jobs WHERE id=?`

### เช็ค Logs
```bash
# App logs
docker compose -f docker-compose.prod.yml logs app --tail=50

# Scheduler logs  
docker compose -f docker-compose.prod.yml logs scheduler --tail=50

# MDR Alert error
docker compose -f docker-compose.prod.yml exec mysql mysql -u root -p -e \
"SELECT l.status, l.error_message, l.run_at FROM schedule_job_logs l JOIN schedule_jobs j ON j.id=l.schedule_job_id WHERE j.name='MDR Alert' ORDER BY l.run_at DESC LIMIT 5;" bk_moph_notify
```
