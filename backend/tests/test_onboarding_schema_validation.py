"""Tests for onboarding schema numeric validation limits."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.onboarding import ProfileRequest


def _base() -> dict:
    return {
        "full_name": "علی احمدی",
        "gender": "male",
        "age": 25,
        "height_cm": 175.0,
        "current_weight_kg": 70.0,
    }


def test_age_below_min_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "age": 7})


def test_age_min_accepted():
    p = ProfileRequest(**{**_base(), "age": 8})
    assert p.age == 8


def test_age_max_accepted():
    p = ProfileRequest(**{**_base(), "age": 120})
    assert p.age == 120


def test_age_above_max_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "age": 121})


def test_negative_height_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "height_cm": -10.0})


def test_height_below_min_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "height_cm": 79.0})


def test_height_min_accepted():
    p = ProfileRequest(**{**_base(), "height_cm": 80.0})
    assert p.height_cm == 80.0


def test_height_max_accepted():
    p = ProfileRequest(**{**_base(), "height_cm": 230.0})
    assert p.height_cm == 230.0


def test_height_above_max_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "height_cm": 231.0})


def test_negative_weight_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "current_weight_kg": -5.0})


def test_weight_below_min_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "current_weight_kg": 19.9})


def test_negative_target_weight_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "target_weight_kg": -1.0})


def test_target_weight_optional_none_accepted():
    p = ProfileRequest(**{**_base(), "target_weight_kg": None})
    assert p.target_weight_kg is None


def test_negative_waist_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "waist_circumference_cm": -5.0})


def test_waist_optional_none_accepted():
    p = ProfileRequest(**{**_base(), "waist_circumference_cm": None})
    assert p.waist_circumference_cm is None


def test_negative_wrist_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "wrist_circumference_cm": -1.0})


def test_wrist_below_min_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "wrist_circumference_cm": 7.9})


def test_wrist_min_accepted():
    p = ProfileRequest(**{**_base(), "wrist_circumference_cm": 8.0})
    assert p.wrist_circumference_cm == 8.0


def test_wrist_max_accepted():
    p = ProfileRequest(**{**_base(), "wrist_circumference_cm": 35.0})
    assert p.wrist_circumference_cm == 35.0


def test_wrist_above_max_rejected():
    with pytest.raises(ValidationError):
        ProfileRequest(**{**_base(), "wrist_circumference_cm": 35.1})


def test_wrist_optional_none_accepted():
    p = ProfileRequest(**{**_base(), "wrist_circumference_cm": None})
    assert p.wrist_circumference_cm is None


def test_no_age_or_birth_date_rejected():
    data = _base()
    del data["age"]
    with pytest.raises(ValidationError):
        ProfileRequest(**data)
