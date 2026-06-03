"""Tests for Phase 9 progress endpoints (PROG-01, PROG-02, PROG-03)."""
from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy import select
from app.models.progress import DailyCheckIn


def test_submit_check_in(client, auth_headers, test_user, db_session):
    """PROG-01: A valid check-in creates exactly one DailyCheckIn row and returns 201."""
    today = date.today().isoformat()
    body = {
        "check_date": today,
        "weight_kg": 72.5,
        "hunger_level": 2,
        "sleep_hours": 7.5,
        "stress_level": 2,
        "activity_minutes": 45,
        "adherence_notes": "روز خوبی بود",
    }
    res = client.post("/api/v1/progress/check-in", json=body, headers=auth_headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["weight_kg"] == 72.5
    assert data["hunger_level"] == 2
    assert data["sleep_hours"] == 7.5
    assert data["adherence_notes"] == "روز خوبی بود"
    assert data["check_date"] == today

    rows = db_session.execute(
        select(DailyCheckIn).where(DailyCheckIn.user_id == test_user.id)
    ).scalars().all()
    assert len(rows) == 1


def test_checkin_upsert(client, auth_headers, test_user, db_session):
    """PROG-01: Two submissions on the same day must upsert — never duplicate."""
    today = date.today().isoformat()
    r1 = client.post(
        "/api/v1/progress/check-in",
        json={"check_date": today, "weight_kg": 72.5, "sleep_hours": 7.0},
        headers=auth_headers,
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/progress/check-in",
        json={"check_date": today, "weight_kg": 72.1, "sleep_hours": 8.0},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    assert r2.json()["weight_kg"] == 72.1
    assert r2.json()["sleep_hours"] == 8.0

    rows = db_session.execute(
        select(DailyCheckIn).where(DailyCheckIn.user_id == test_user.id)
    ).scalars().all()
    assert len(rows) == 1, f"Expected 1 row after upsert, got {len(rows)}"
    assert rows[0].weight_kg == 72.1


def test_unauthenticated_returns_401(unauth_client):
    """Bearer token is required for all progress endpoints."""
    res = unauth_client.get("/api/v1/progress/summary")
    assert res.status_code == 401, res.text


def test_progress_summary(client, auth_headers, test_user, db_session):
    """PROG-02: Summary returns weight series, behavior wins, and logging streak."""
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        client.post(
            "/api/v1/progress/check-in",
            json={
                "check_date": d,
                "weight_kg": 73.0 - i * 0.2,
                "sleep_hours": 7.5,
                "activity_minutes": 35,
                "hunger_level": 2,
                "stress_level": 2,
            },
            headers=auth_headers,
        )
    res = client.get("/api/v1/progress/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_data"] is True
    assert len(data["weight_series"]) == 3
    assert data["latest_weight_kg"] == 73.0
    assert len(data["behavior_wins"]) == 8
    keys = {w["key"] for w in data["behavior_wins"]}
    assert {"sleep", "activity", "logging", "low_stress", "low_hunger", "protein", "fiber", "hydration"} == keys
    assert data["logging_streak"] >= 1
    untracked = [w for w in data["behavior_wins"] if w["tracked"] is False]
    assert len(untracked) == 3


def test_progress_summary_empty(client, auth_headers, test_user):
    """PROG-02: Empty state for users with zero check-ins."""
    res = client.get("/api/v1/progress/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_data"] is False
    assert data["weight_series"] == []
    assert data["recent_checkins"] == []
    assert data["logging_streak"] == 0
    assert isinstance(data["empty_state_message"], str)
    assert len(data["empty_state_message"]) > 0


def test_weekly_report(client, auth_headers, test_user, db_session):
    """PROG-03: 7 check-ins for the current week → full weekly report."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    for i in range(7):
        d = (week_start + timedelta(days=i)).isoformat()
        client.post(
            "/api/v1/progress/check-in",
            json={
                "check_date": d,
                "weight_kg": 73.0 - i * 0.1,
                "sleep_hours": 7.5,
                "stress_level": 2,
                "hunger_level": 2,
                "activity_minutes": 40,
            },
            headers=auth_headers,
        )
    res = client.get("/api/v1/progress/weekly-report", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_report"] is True
    report = data["report"]
    assert report["logging_days"] == 7
    assert report["adherence_pct"] == 100
    assert report["avg_sleep"] == 7.5
    assert report["avg_stress"] == 2.0
    assert report["total_activity_minutes"] == 280
    assert isinstance(report["suggested_focus"], str)
    assert len(report["suggested_focus"]) > 0
    assert report["weight_trend"] is not None
    assert report["weight_trend"]["first"] == 73.0


def test_weekly_report_empty(client, auth_headers, test_user):
    """PROG-03: Empty state when no check-ins exist this week."""
    res = client.get("/api/v1/progress/weekly-report", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["has_report"] is False
    assert isinstance(data["empty_state_message"], str)
    assert len(data["empty_state_message"]) > 0
    assert data["week_start"] is not None
    assert data["week_end"] is not None
