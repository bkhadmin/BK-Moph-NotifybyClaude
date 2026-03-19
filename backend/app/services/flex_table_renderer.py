from datetime import datetime
from app.utils.thai_datetime import bangkok_now, format_thai_datetime

def _date_text(rows):
    if rows and isinstance(rows[0], dict):
        return rows[0].get("วันนัด") or rows[0].get("appointment_date") or "-"
    return "-"

def _chunk(rows, size):
    for i in range(0, len(rows), size):
        yield rows[i:i+size], i

def build_full_table_flex(rows:list[dict], title:str="จำนวนผู้ป่วยนัดแยกรายคลินิก", chunk_size:int=8):
    if not rows:
        rows = [{}]
    appt_date = _date_text(rows)
    sent_at = format_thai_datetime(bangkok_now())
    bubbles = []
    for chunk, offset in _chunk(rows, chunk_size):
        contents = [
            {"type":"text","text":title,"weight":"bold","size":"lg","wrap":True},
            {"type":"text","text":f"วันที่ {appt_date}","size":"sm","color":"#2563eb","margin":"md","wrap":True},
            {"type":"text","text":f"ส่งเมื่อ {sent_at}","size":"xs","color":"#64748b","margin":"sm","wrap":True},
            {"type":"separator","margin":"md"},
            {
                "type":"box","layout":"baseline","margin":"md",
                "contents":[
                    {"type":"text","text":"คลินิก","weight":"bold","size":"sm","flex":5},
                    {"type":"text","text":"จำนวน","weight":"bold","size":"sm","flex":2,"align":"end"}
                ]
            },
            {"type":"separator","margin":"sm"},
        ]
        for idx, row in enumerate(chunk, start=offset+1):
            clinic = row.get("clinic_name","-")
            dept = row.get("department","-")
            total = row.get("total_appointment",0)
            contents.extend([
                {
                    "type":"box","layout":"baseline","margin":"md",
                    "contents":[
                        {"type":"text","text":clinic,"size":"sm","weight":"bold","flex":5,"wrap":True,"color":"#0f172a"},
                        {"type":"text","text":str(total),"size":"sm","weight":"bold","flex":2,"align":"end","color":"#16a34a"}
                    ]
                },
                {"type":"text","text":dept,"size":"xs","color":"#64748b","wrap":True,"margin":"sm"},
                {"type":"separator","margin":"md"}
            ])
        if offset > 0:
            contents.insert(3, {"type":"text","text":f"หน้าที่ {offset//chunk_size + 1}","size":"xs","color":"#94a3b8","margin":"sm"})
        bubbles.append({"type":"bubble","body":{"type":"box","layout":"vertical","contents":contents}})
    return bubbles[0] if len(bubbles) == 1 else {"type":"carousel","contents":bubbles}
