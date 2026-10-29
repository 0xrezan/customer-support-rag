"""Start the FastAPI server.

Uses --reload in development, multiple workers in production.
"""

import os

import uvicorn

from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    is_production = os.getenv("APP_ENV", "development") == "production"

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not is_production,
        reload_dirs=["app", "scripts"] if not is_production else None,
        workers=int(os.getenv("API_WORKERS", "4")) if is_production else 1,
        log_level="info" if is_production else "debug",
        access_log=is_production,
    )
