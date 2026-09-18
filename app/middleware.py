"""HTTP middleware applied to every response.

Security headers are set here rather than per-route, so every page — including
ones not written yet — inherits them by default rather than by remembering to
opt in.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# Content-Security-Policy: what the browser is allowed to load, and from where.
# Everything currently comes from this origin (the one stylesheet), so 'self'
# alone is enough. Revisit when a CDN, embedded video, or Alpine.js arrives —
# Alpine's standard build needs 'unsafe-eval' unless its CSP build is used.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)

# FastAPI's auto-generated docs pages load Swagger UI / ReDoc from a public
# CDN, which `default-src 'self'` blocks — the page would render blank. These
# routes only exist in development (see `app/main.py`), so skipping CSP for
# them costs nothing in production, where they aren't registered at all.
CSP_EXEMPT_PATHS = frozenset({"/docs", "/redoc", "/docs/oauth2-redirect"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        if request.url.path not in CSP_EXEMPT_PATHS:
            response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        # Don't let the browser second-guess a declared content type.
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Belt-and-braces with frame-ancestors above, for older browsers.
        response.headers["X-Frame-Options"] = "DENY"
        # Send the full URL as referrer only within this site.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS tells a browser to only ever use HTTPS for this host. Setting it
        # in local development would make the browser force https://localhost,
        # which has no certificate and simply breaks — so production only.
        if settings.environment != "development":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response
