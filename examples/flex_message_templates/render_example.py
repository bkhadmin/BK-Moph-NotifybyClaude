import json
from datetime import datetime
from pathlib import Path

sample_rows = json.loads(Path("examples/appointments_sample.json").read_text(encoding="utf-8"))
template = json.loads(Path("examples/flex_message_templates/appointment_single_bubble.json").read_text(encoding="utf-8"))

sent_at = datetime.now().strftime("%d/%m/%Y %H:%M น.")

def apply_value(obj, mapping):
    if isinstance(obj, dict):
        return {k: apply_value(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [apply_value(x, mapping) for x in obj]
    if isinstance(obj, str):
        for k, v in mapping.items():
            obj = obj.replace("{" + k + "}", str(v))
        return obj
    return obj

row = sample_rows[0]
mapping = {
    "clinic_name": row["clinic_name"],
    "department": row["department"],
    "total_appointment": row["total_appointment"],
    "sent_at": sent_at,
}

result = apply_value(template, mapping)
print(json.dumps(result, ensure_ascii=False, indent=2))
