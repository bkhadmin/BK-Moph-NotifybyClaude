import secrets
from pathlib import Path
from PIL import Image
from app.core.config import settings

def save_resized_image(file_bytes:bytes, original_name:str, mime_type:str|None):
    ext = Path(original_name).suffix.lower() or '.jpg'
    stored_name = f"{secrets.token_hex(16)}{ext}"
    output_path = settings.upload_path / stored_name
    with Image.open(__import__('io').BytesIO(file_bytes)) as im:
        im = im.convert('RGB')
        im.thumbnail((1024, 1024))
        im.save(output_path, quality=85, optimize=True)
        width, height = im.size
    return {
        "stored_name": stored_name,
        "width": width,
        "height": height,
        "public_url": f"{settings.image_public_base}/{stored_name}",
        "mime_type": mime_type or "image/jpeg",
    }
