"""FastAPI application factory for TrustDesk.
Technical demonstration on synthetic data - not a regulated banking system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.config import settings


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

    app.include_router(api_router)
    return app


app = create_app()
