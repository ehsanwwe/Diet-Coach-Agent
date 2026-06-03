"""Tests for Phase 9 progress endpoints (PROG-01, PROG-02, PROG-03)."""
import pytest


@pytest.mark.skip(reason="Implemented in Task 4 after production code")
def test_submit_check_in(client, auth_headers, test_user, db_session): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_checkin_upsert(client, auth_headers, test_user, db_session): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_unauthenticated_returns_401(unauth_client): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_progress_summary(client, auth_headers, test_user, db_session): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_progress_summary_empty(client, auth_headers, test_user): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_weekly_report(client, auth_headers, test_user, db_session): ...


@pytest.mark.skip(reason="Implemented in Task 4")
def test_weekly_report_empty(client, auth_headers, test_user): ...
