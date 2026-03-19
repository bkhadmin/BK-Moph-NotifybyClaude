from io import BytesIO
from openpyxl import Workbook

def to_xlsx_bytes(rows:list[dict], sheet_name:str="data")->bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    if not rows:
        ws.append(["no_data"])
    else:
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
    out = BytesIO()
    wb.save(out)
    return out.getvalue()
