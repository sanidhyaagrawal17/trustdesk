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

    dist_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

    @app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
    async def favicon():
        favicon_path = dist_dir / "favicon.svg"
        if favicon_path.exists():
            from fastapi.responses import FileResponse
            return FileResponse(favicon_path, media_type="image/svg+xml")
        from fastapi.responses import Response
        return Response(status_code=204)

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    async def serve_index():
        index_file = dist_dir / "index.html"
        if index_file.exists():
            from fastapi.responses import FileResponse
            return FileResponse(
                index_file,
                media_type="text/html",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )
        from fastapi.responses import JSONResponse
        return JSONResponse({"status": "TrustDesk backend running. Build frontend with 'npm run build'."})

    @app.api_route("/assets/{file_name}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_asset(file_name: str):
        asset_path = dist_dir / "assets" / file_name
        from fastapi.responses import FileResponse
        if asset_path.exists():
            media_type = "text/css" if file_name.endswith(".css") else ("application/javascript" if file_name.endswith(".js") else None)
            return FileResponse(asset_path, media_type=media_type)
        # Fallback to the latest CSS or JS asset if a cached browser requests an older asset hash
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            ext = ".css" if file_name.endswith(".css") else (".js" if file_name.endswith(".js") else None)
            if ext:
                matching = sorted(assets_dir.glob(f"*{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
                if matching:
                    media_type = "text/css" if ext == ".css" else "application/javascript"
                    return FileResponse(matching[0], media_type=media_type)
        from fastapi.responses import Response
        return Response(status_code=404)

    app.include_router(api_router)

    # Mount compiled React build if dist exists
    if dist_dir.exists():
        app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")

    return app


app = create_app()
