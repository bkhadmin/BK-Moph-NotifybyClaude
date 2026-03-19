from starlette.middleware.base import BaseHTTPMiddleware
class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next): return await call_next(request)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response=await call_next(request)
        response.headers['X-Frame-Options']='DENY'
        response.headers['X-Content-Type-Options']='nosniff'
        return response
class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next): return await call_next(request)
