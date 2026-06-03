"""
Central API v1 router. All endpoint routers are registered here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.onboarding import router as onboarding_router

api_router = APIRouter()

# Phase 1: Infrastructure
api_router.include_router(health_router)

# Phase 3: Authentication
api_router.include_router(auth_router, prefix="/auth")

# Phase 4: Onboarding
api_router.include_router(onboarding_router, prefix="/onboarding")
