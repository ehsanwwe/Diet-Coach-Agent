"""Progress API endpoints — Phase 9. PROG-01, PROG-02, PROG-03.

All endpoints require a valid Bearer token via get_current_user.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_session
from app.core.errors import AppError, raise_http_error
from app.models.user import User
from app.schemas.progress import (
    CheckInRequest,
    CheckInResponse,
    ProgressSummaryResponse,
    WeeklyReportResponse,
)
from app.services import progress_service

router = APIRouter(tags=["progress"])


@router.post("/check-in", response_model=CheckInResponse, status_code=201)
def submit_check_in(
    body: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> CheckInResponse:
    """Submit or update today's daily check-in (PROG-01)."""
    try:
        return progress_service.submit_check_in(db, current_user, body)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Check-in failed: {exc}", status_code=500)


@router.get("/summary", response_model=ProgressSummaryResponse)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> ProgressSummaryResponse:
    """Return progress summary with behavior wins and weight series (PROG-02, PROG-04, PROG-05)."""
    try:
        return progress_service.get_summary(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Summary failed: {exc}", status_code=500)


@router.get("/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> WeeklyReportResponse:
    """Return the current-week aggregated report (PROG-03)."""
    try:
        return progress_service.get_weekly_report(db, current_user)
    except AppError as exc:
        raise_http_error(exc.message, status_code=exc.status_code)
    except Exception as exc:
        raise_http_error(f"Weekly report failed: {exc}", status_code=500)
