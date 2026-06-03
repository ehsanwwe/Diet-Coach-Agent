"""
Health check endpoint.

GET /api/v1/health - Returns service status.
Used by load balancers and monitoring (no auth required).
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """
    Returns 200 OK with service status.
    This endpoint requires no authentication.
    """
    return {"status": "ok", "service": "diet-coach-agent"}
