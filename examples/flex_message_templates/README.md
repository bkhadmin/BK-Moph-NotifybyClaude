# ตัวอย่างการใช้ Flex Message กับผล Query นัดหมาย

## 1) กรณีส่งทีละคลินิก
ใช้ไฟล์:
- `appointment_single_bubble.json`
- `appointment_summary_carousel.json`

### mapping field
- `{clinic_name}` = คลินิก
- `{department}` = แผนกที่นัด
- `{total_appointment}` = จำนวนผู้ป่วยที่นัด
- `{sent_at}` = วันที่และเวลาที่ส่งข้อความ

ตัวอย่างค่า `sent_at`
- `15/03/2026 19:30 น.`

## 2) กรณีส่งสรุป Top 5 ในข้อความเดียว
ใช้ไฟล์:
- `appointment_top5_dashboard.json`

### mapping field
- `{row1_clinic_name}`
- `{row1_total_appointment}`
- ...
- `{row5_clinic_name}`
- `{row5_total_appointment}`
- `{sent_at}`

## 3) แนวทางใช้งานจริง
### แบบ carousel
เหมาะเมื่ออยากให้แต่ละคลินิกเป็น 1 card เลื่อนดูได้

### แบบ top 5 dashboard
เหมาะเมื่ออยากสรุปภาพรวมสั้น ๆ ในข้อความเดียว

## 4) ตัวอย่างข้อความประกอบ
`สรุปยอดผู้ป่วยนัดหมายประจำวัน ส่งเมื่อ {sent_at}`
