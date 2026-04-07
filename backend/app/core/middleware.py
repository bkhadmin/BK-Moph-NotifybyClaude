import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

_access_log = logging.getLogger("access")

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = round((time.perf_counter() - start) * 1000)
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "-")
        _access_log.info("%s %s %s %dms", request.method, request.url.path, response.status_code, ms,
                         extra={"ip": ip})
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next): return await call_next(request)
