from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.endpoints import web
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.middleware import AccessLogMiddleware, CSRFMiddleware, SecurityHeadersMiddleware

app = FastAPI(title=settings.app_name, debug=settings.app_debug)
settings.upload_path.mkdir(parents=True, exist_ok=True)

# ── Auto migration: เพิ่ม column ใหม่ที่ยังไม่มีใน DB ────────────────────
def _run_migrations():
    from app.db.session import engine
    migrations = [
        "ALTER TABLE notify_rooms ADD COLUMN channel_type VARCHAR(20) NOT NULL DEFAULT 'moph_notify'",
        "ALTER TABLE notify_rooms MODIFY COLUMN secret_key TEXT NULL",
        """CREATE TABLE IF NOT EXISTS line_users (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            line_uid     VARCHAR(64) NOT NULL UNIQUE,
            display_name VARCHAR(200),
            real_name    VARCHAR(200),
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        "ALTER TABLE schedule_jobs ADD COLUMN use_alertroom VARCHAR(1) NOT NULL DEFAULT 'N'",
        "ALTER TABLE alert_cases MODIFY COLUMN item_name TEXT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(__import__('sqlalchemy').text(sql))
                conn.commit()
            except Exception:
                conn.rollback()  # column มีอยู่แล้ว หรือ error อื่น — ข้ามไป

try:
    _run_migrations()
except Exception:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trusted_hosts = [x.strip() for x in settings.trusted_hosts.split(",") if x.strip()]
for h in ["app", "app:8000", "nginx", "bk_app", "127.0.0.1", "127.0.0.1:8000", "localhost"]:
    if h not in trusted_hosts:
        trusted_hosts.append(h)

public_url = (getattr(settings, "public_base_url", None) or "").strip()
if public_url:
    try:
        host = urlparse(public_url).netloc.strip()
        if host and host not in trusted_hosts:
            trusted_hosts.append(host)
    except Exception:
        pass

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts or ["*"])
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(AccessLogMiddleware)

app.mount("/static/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

app.include_router(api_router, prefix="/api/v1")
app.include_router(web.router)
