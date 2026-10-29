"""FastAPI application entrypoint."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.lifespan import lifespan
from app.logging import correlation_id_ctx


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inject a correlation ID from X-Request-ID header or generate one."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id_ctx.set(request_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def create_app() -> FastAPI:
    """Application factory."""

    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Middleware (outermost first)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(CorrelationIDMiddleware)

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    # Register API routers (imported lazily to keep module-level imports light)
    from app.api.admin_routes import router as admin_router
    from app.api.chat_routes import router as chat_router
    from app.api.feedback_routes import router as feedback_router
    from app.api.health_routes import router as health_router

    prefix = settings.api_prefix
    application.include_router(health_router, prefix=prefix, tags=["health"])
    application.include_router(admin_router, prefix=prefix, tags=["admin"])
    application.include_router(chat_router, prefix=prefix, tags=["chat"])
    application.include_router(feedback_router, prefix=prefix, tags=["feedback"])

    # Phase 2 routes
    from app.api.admin_dashboard import router as dashboard_router
    from app.api.bulk_routes import router as bulk_router

    application.include_router(dashboard_router, prefix=prefix, tags=["dashboard"])
    application.include_router(bulk_router, prefix=prefix, tags=["admin-bulk"])

    # Telegram webhook (enabled via config)
    if settings.telegram_webhook_enabled:
        from app.api.telegram_webhook import router as webhook_router

        application.include_router(webhook_router, prefix=prefix, tags=["telegram"])

    # Register exception handlers
    from app.api.errors import register_exception_handlers

    register_exception_handlers(application)

    return application


app = create_app()
