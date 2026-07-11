"""Backend guardrails: female-only onboarding values must not be persisted for
non-female profiles, and status must expose gender for the frontend."""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import onboarding_repository
from app.schemas.onboarding import (
    FEMALE_ONLY_GOAL_TYPES,
    FEMALE_ONLY_MEDICAL_FIELDS,
    GoalRequest,
    MedicalRequest,
    ProfileRequest,
)
from app.services import onboarding_service


def _base_profile(gender: str = "male") -> ProfileRequest:
    return ProfileRequest(
        full_name="Test User",
        gender=gender,  # type: ignore[arg-type]
        age=30,
        height_cm=175.0,
        current_weight_kg=70.0,
    )


def _flags_by_code(db: Session, user_id: str) -> dict[str, bool]:
    return {
        f.condition_code: f.has_condition
        for f in onboarding_repository.get_medical_flags(db, user_id)
    }


def _saved_goal_types(db: Session, user_id: str) -> list[str]:
    goal = onboarding_repository.get_nutrition_goal(db, user_id)
    assert goal is not None and goal.goal_types_json is not None
    import json as _json
    return _json.loads(goal.goal_types_json)


def test_status_exposes_gender_when_profile_saved(db_session: Session, test_user: User):
    onboarding_service.save_profile(db_session, test_user, _base_profile("female"))

    status = onboarding_service.get_status(db_session, test_user)

    assert status.gender == "female"


def test_status_gender_is_none_before_profile(db_session: Session, test_user: User):
    status = onboarding_service.get_status(db_session, test_user)
    assert status.gender is None


def test_female_user_can_save_female_only_goals(db_session: Session, test_user: User):
    onboarding_service.save_profile(db_session, test_user, _base_profile("female"))

    resp = onboarding_service.save_goals(
        db_session,
        test_user,
        GoalRequest(goal_types=["weight_loss", "pcos_support", "pregnancy_breastfeeding_caution"]),
    )

    assert set(resp.goal_types) == {
        "weight_loss",
        "pcos_support",
        "pregnancy_breastfeeding_caution",
    }
    stored = _saved_goal_types(db_session, test_user.id)
    assert set(stored) == set(resp.goal_types)


@pytest.mark.parametrize("gender", ["male", "other", "prefer_not_to_say"])
def test_non_female_user_cannot_store_female_only_goals(
    db_session: Session, test_user: User, gender: str
):
    onboarding_service.save_profile(db_session, test_user, _base_profile(gender))

    resp = onboarding_service.save_goals(
        db_session,
        test_user,
        GoalRequest(goal_types=["weight_loss", "pcos_support", "pregnancy_breastfeeding_caution"]),
    )

    assert set(resp.goal_types) == {"weight_loss"}
    stored = _saved_goal_types(db_session, test_user.id)
    assert set(stored).isdisjoint(FEMALE_ONLY_GOAL_TYPES)


def test_female_user_can_save_female_only_medical(db_session: Session, test_user: User):
    onboarding_service.save_profile(db_session, test_user, _base_profile("female"))

    onboarding_service.save_medical(
        db_session,
        test_user,
        MedicalRequest(pcos=True, pregnancy_breastfeeding=True),
    )

    flags = _flags_by_code(db_session, test_user.id)
    assert flags["pcos"] is True
    assert flags["pregnancy_breastfeeding"] is True


@pytest.mark.parametrize("gender", ["male", "other", "prefer_not_to_say"])
def test_non_female_user_cannot_store_female_only_medical(
    db_session: Session, test_user: User, gender: str
):
    onboarding_service.save_profile(db_session, test_user, _base_profile(gender))

    onboarding_service.save_medical(
        db_session,
        test_user,
        MedicalRequest(
            diabetes=True,
            pcos=True,
            pregnancy_breastfeeding=True,
        ),
    )

    flags = _flags_by_code(db_session, test_user.id)
    assert flags["diabetes"] is True
    for k in FEMALE_ONLY_MEDICAL_FIELDS:
        assert flags[k] is False


def test_changing_gender_from_female_scrubs_saved_female_only_values(
    db_session: Session, test_user: User
):
    # Female profile with female-only goals and medical flags
    onboarding_service.save_profile(db_session, test_user, _base_profile("female"))
    onboarding_service.save_goals(
        db_session,
        test_user,
        GoalRequest(goal_types=["weight_loss", "pcos_support", "pregnancy_breastfeeding_caution"]),
    )
    onboarding_service.save_medical(
        db_session,
        test_user,
        MedicalRequest(pcos=True, pregnancy_breastfeeding=True),
    )

    # Change gender to male — service should purge previously saved female-only rows
    onboarding_service.save_profile(db_session, test_user, _base_profile("male"))

    stored_goals = _saved_goal_types(db_session, test_user.id)
    assert set(stored_goals) == {"weight_loss"}

    flags = _flags_by_code(db_session, test_user.id)
    for k in FEMALE_ONLY_MEDICAL_FIELDS:
        assert flags[k] is False


def test_only_female_only_goals_rejects_empty_after_filter(
    db_session: Session, test_user: User
):
    onboarding_service.save_profile(db_session, test_user, _base_profile("male"))

    with pytest.raises(Exception):
        onboarding_service.save_goals(
            db_session,
            test_user,
            GoalRequest(goal_types=["pcos_support"]),
        )
