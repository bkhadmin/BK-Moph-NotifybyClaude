import json

SIZE_MAP = {
    "xs":"xs","sm":"sm","md":"md","lg":"lg","xl":"xl","xxl":"xxl","3xl":"3xl","4xl":"4xl"
}

def build_bubble(
    title:str='',
    subtitle:str='',
    body_text:str='',
    hero_image_url:str='',
    button_label:str='',
    button_url:str='',
    title_color:str='#0f172a',
    subtitle_color:str='#64748b',
    body_color:str='#334155',
    accent_color:str='#2563eb',
    title_size:str='lg',
    body_size:str='md',
):
    bubble = {"type":"bubble","body":{"type":"box","layout":"vertical","contents":[]}}
    contents = bubble["body"]["contents"]
    if title:
        contents.append({
            "type":"text","text":title,"weight":"bold","size":SIZE_MAP.get(title_size, 'lg'),
            "color":title_color,"wrap":True
        })
    if subtitle:
        contents.append({
            "type":"text","text":subtitle,"size":"sm","color":subtitle_color,
            "wrap":True,"margin":"md"
        })
    if body_text:
        for idx, line in enumerate((body_text or '').splitlines()):
            if line.strip():
                contents.append({
                    "type":"text","text":line,"size":SIZE_MAP.get(body_size, 'md'),
                    "color":body_color,"wrap":True,"margin":"md" if idx == 0 else "sm"
                })
    if hero_image_url:
        bubble["hero"] = {
            "type":"image","url":hero_image_url,"size":"full",
            "aspectMode":"cover","aspectRatio":"20:13"
        }
    if button_label and button_url:
        bubble["footer"] = {
            "type":"box","layout":"vertical","contents":[
                {"type":"button","style":"primary","color":accent_color,
                 "action":{"type":"uri","label":button_label,"uri":button_url}}
            ]
        }
    return bubble

def template_json_from_bubble(bubble:dict) -> str:
    return json.dumps(bubble, ensure_ascii=False, indent=2)
