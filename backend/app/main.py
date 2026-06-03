"""
FastAPI application factory for Diet Coach Agent.

This module creates and configures the FastAPI app instance.
Run with: uvicorn app.main:app --reload (from backend/ directory)

BE-01: CORS configured from environment variables (never hard-coded)
BE-08: Global exception handler ensures consistent error response format
BE-10: OpenAPI docs enabled at /docs
BE-12: SECRET_KEY validated at import time via settings instantiation
INFRA-05: uvicorn app.main:app from backend/ starts the server
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# BE-12: Importing settings triggers SECRET_KEY validation.
# If SECRET_KEY is missing or placeholder, this raises ValueError
# and the process exits before the server starts.
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import AppError


def create_app() -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI instance.

    Separated from module-level instantiation to allow test overrides.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered multilingual nutrition companion",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS Middleware (BE-01)
    # Origins loaded from CORS_ORIGINS env var, never hard-coded.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    )

    # Global Exception Handlers (BE-08)
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Catch AppError and return standard error response shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Catch all unhandled exceptions.
        Returns 500 with standard error shape and never exposes stack traces.
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "An unexpected error occurred. Please try again.",
                "detail": {},
            },
        )

    # API Routes (BE-09)
    # All API routes are versioned under /api/v1.
    app.include_router(api_router, prefix="/api/v1")

    return app


# Module-level app instance used by uvicorn app.main:app.
app = create_app()
