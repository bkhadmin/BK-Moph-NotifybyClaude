# Cloudflare Tunnel Example

ตัวอย่างการเปิด public endpoint สำหรับรับเคสจากภายนอก

## เป้าหมาย
ให้ลิงก์ใน Flex Message เป็น public URL เช่น

`https://alert.bkhospital.go.th/alerts/claim?case_key=...`

## เงื่อนไข
- โดเมนหรือ subdomain ต้องอยู่บน Cloudflare DNS
- server ภายในรัน BK-Moph-Notify ที่พอร์ต 8012

## ขั้นตอนย่อ
1. ติดตั้ง `cloudflared`
2. รัน `cloudflared tunnel login`
3. รัน `cloudflared tunnel create bk-moph-notify`
4. แก้ `config.yml` ตามตัวอย่าง
5. รัน
   - `cloudflared tunnel route dns bk-moph-notify alert.bkhospital.go.th`
   - `cloudflared service install`
   - `systemctl enable --now cloudflared`

## ENV ที่ต้องตั้งในระบบ
`.env`
```env
PUBLIC_BASE_URL=https://alert.bkhospital.go.th
```

เมื่อกำหนดแล้ว ระบบจะใช้ URL นี้ในการสร้าง `{claim_url}`
แทน private IP เช่น `http://192.168.191.12`
