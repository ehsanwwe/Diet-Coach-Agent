from __future__ import annotations

from app.services import safety_guardrail_service as guardrails


def _assess(
    flags: dict[str, bool] | None = None,
    meds: list[str] | None = None,
    symptoms: list[str] | None = None,
    age: int | None = None,
):
    return guardrails.assess(flags or {}, meds or [], symptoms or [], age=age)


def test_cancer_requires_clinical_review():
    result = _assess({"cancer": True})
    assert result.risk_level == "clinical_review_required"
    assert "cancer" in result.flags_triggered


def test_complex_heart_condition_requires_clinical_review():
    result = _assess(symptoms=["history of heart failure"])
    assert result.risk_level == "clinical_review_required"
    assert "complex_heart_disease" in result.flags_triggered


def test_uncontrolled_thyroid_requires_clinical_review_persian():
    result = _assess(symptoms=["تیروئید کنترل‌نشده دارم"])
    assert result.risk_level == "clinical_review_required"
    assert "uncontrolled_thyroid_disorder" in result.flags_triggered


def test_advanced_liver_disease_requires_clinical_review():
    result = _assess(symptoms=["advanced liver disease and cirrhosis"])
    assert result.risk_level == "clinical_review_required"
    assert "advanced_liver_disease" in result.flags_triggered


def test_diabetes_with_insulin_requires_clinical_review():
    result = _assess({"diabetes": True}, meds=["insulin"])
    assert result.risk_level == "clinical_review_required"
    assert "diabetes_with_medication" in result.flags_triggered


def test_diabetes_medication_detected_in_english_and_persian():
    english = _assess({"diabetes": True}, meds=["metformin"])
    persian = _assess({"diabetes": True}, meds=["متفورمین"])

    assert english.risk_level == "clinical_review_required"
    assert persian.risk_level == "clinical_review_required"
    assert "diabetes_with_medication" in english.flags_triggered
    assert "diabetes_with_medication" in persian.flags_triggered


def test_dangerous_calorie_restriction_requires_clinical_review():
    result = _assess(symptoms=["I want an 800 calories per day diet"])
    assert result.risk_level == "clinical_review_required"
    assert "dangerous_calorie_restriction" in result.flags_triggered
