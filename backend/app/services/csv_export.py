import csv
import io

def to_csv_bytes(rows:list[dict]) -> bytes:
    buffer = io.StringIO()
    if not rows:
        buffer.write("no_data\n")
        return buffer.getvalue().encode("utf-8-sig")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8-sig")
