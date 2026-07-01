"""
Central API v1 router. All endpoint routers are registered here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.admin_auth import router as admin_auth_router
from app.api.v1.endpoints.admin_users import router as admin_users_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.nutrition import router as nutrition_router
from app.api.v1.endpoints.onboarding import router as onboarding_router
from app.api.v1.endpoints.onboarding_chat import router as onboarding_chat_router
from app.api.v1.endpoints.progress import router as progress_router
from app.api.v1.endpoints.settings import router as settings_router

api_router = APIRouter()

# Phase 1: Infrastructure
api_router.include_router(health_router)

# Phase 3: Authentication
api_router.include_router(auth_router, prefix="/auth")

# Phase 4: Onboarding
api_router.include_router(onboarding_router, prefix="/onboarding")

# Phase 6: Voice & Audio
api_router.include_router(onboarding_chat_router, prefix="/onboarding")

# Phase 7: Nutrition Backend & AI Layer
api_router.include_router(nutrition_router, prefix="/nutrition")

# Phase 8: Companion Chat
api_router.include_router(chat_router, prefix="/chat")

# Phase 9: Progress & Reports
api_router.include_router(progress_router, prefix="/progress")

# Phase 10: Settings, Polish & Remaining UI
api_router.include_router(settings_router, prefix="/settings")

# Admin panel (separate auth, hidden from normal users)
_admin_router = APIRouter(prefix="/admin")
_admin_router.include_router(admin_auth_router, prefix="/auth")
_admin_router.include_router(admin_users_router, prefix="/users")
api_router.include_router(_admin_router)
