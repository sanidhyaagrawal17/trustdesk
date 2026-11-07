"""FastAPI application factory for TrustDesk.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router as api_router
from backend.audit.audit_logger import audit_logger
from backend.config import settings
from backend.state.session_store import session_store


def create_app() -> FastAPI:
    """Creates and configures the FastAPI application."""
    app = FastAPI(
        title="TrustDesk",
        description="Loan-FAQ conversational assistant technical demonstration on synthetic data. Not a regulated banking system.",
        version="0.1.0",
    )

    # Enable CORS for React Vite development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def root_health():
        return {
            "status": "healthy",
            "service": "TrustDesk",
            "environment": "synthetic_demonstration",
            "regulatory_notice": "TrustDesk is a technical demonstration on synthetic data, not a regulated banking system.",
            "storage_adapters": {
                "session_store": session_store.backend_type,
                "audit_logger": audit_logger.backend_type,
            },
            "features": settings.features,
        }

    @app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
    async def favicon():
        favicon_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "favicon.svg"
        if favicon_path.exists():
            from fastapi.responses import FileResponse
            return FileResponse(favicon_path, media_type="image/svg+xml")
        from fastapi.responses import Response
        return Response(status_code=204)

    app.include_router(api_router)

    # Mount production React build if dist exists
    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
