"""
SafetyGuardrailService: risk-level assessment from onboarding medical data.

Risk levels: low | medium | high | clinical_review_required

This service never gives medical prescriptions or dietary recommendations.
It only classifies risk and records the flags that triggered the classification.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Conditions that always require clinical review before proceeding
CLINICAL_REVIEW_CONDITIONS: frozenset[str] = frozenset(
    {
        "kidney_disease",
        "pregnancy_breastfeeding",
        "eating_disorder_history",
        "bariatric_surgery",
    }
)

# Conditions with diabetes + medication/insulin trigger clinical review
DIABETES_MEDICATION_KEYWORDS: tuple[str, ...] = (
    "insulin",
    "metformin",
    "glipizide",
    "glyburide",
    "sitagliptin",
    "dapagliflozin",
    "empagliflozin",
    "semaglutide",
    "liraglutide",
    "canagliflozin",
    "glimepiride",
    "pioglitazone",
)

# High-risk conditions (not immediately clinical, but flagged as high)
HIGH_RISK_CONDITIONS: frozenset[str] = frozenset(
    {
        "diabetes",
        "liver_disease",
        "thyroid_issues",
    }
)

# Medium-risk conditions
MEDIUM_RISK_CONDITIONS: frozenset[str] = frozenset(
    {
        "high_blood_pressure",
        "high_cholesterol",
        "pcos",
    }
)

# Symptom keywords that trigger clinical review
WARNING_SYMPTOM_KEYWORDS: tuple[str, ...] = (
    "fainting",
    "faint",
    "syncope",
    "chest pain",
    "chest tightness",
    "blood in stool",
    "rectal bleeding",
    "vomiting blood",
    "severe dizziness",
    "severe abdominal",
    "severe nausea",
    "rapid weight loss",
    "unexplained weight loss",
    "self-harm",
    "self harm",
    "suicide",
    "suicidal",
    "heart palpitation",
    "shortness of breath",
    "numbness",
    "severe fatigue",
    "jaundice",
    "yellow skin",
    "yellow eyes",
)


@dataclass
class SafetyAssessment:
    risk_level: str  # low | medium | high | clinical_review_required
    flags_triggered: list[str] = field(default_factory=list)
    clinical_review_required: bool = False


def assess(
    medical_flags: dict[str, bool],
    medications: list[str],
    warning_symptoms: list[str],
    age: int | None = None,
) -> SafetyAssessment:
    """
    Evaluate risk level from structured medical data.

    Returns a SafetyAssessment with the determined risk level and triggered flags.
    Does not recommend treatments, diets, or medical interventions.
    """
    triggered: list[str] = []
    is_clinical = False

    # ── Child/adolescent ────────────────────────────────────────────────────
    if age is not None and age < 18:
        triggered.append("minor_user")
        is_clinical = True

    # ── Clinical review conditions ─────────────────────────────────────────
    for code in CLINICAL_REVIEW_CONDITIONS:
        if medical_flags.get(code, False):
            triggered.append(code)
            is_clinical = True

    # ── Diabetes + any diabetes medication → clinical ───────────────────────
    if medical_flags.get("diabetes", False):
        if "diabetes" not in triggered:
            triggered.append("diabetes")
        med_text = " ".join(m.lower() for m in medications)
        for keyword in DIABETES_MEDICATION_KEYWORDS:
            if keyword in med_text:
                triggered.append("diabetes_with_medication")
                is_clinical = True
                break

    # ── Warning symptoms ───────────────────────────────────────────────────
    symptoms_text = " ".join(s.lower() for s in warning_symptoms)
    for keyword in WARNING_SYMPTOM_KEYWORDS:
        if keyword in symptoms_text:
            triggered.append(f"symptom:{keyword.replace(' ', '_')}")
            is_clinical = True

    # ── Multiple medications (≥3 concurrent prescriptions → high risk) ─────
    # Deduplicate medication names for the count
    unique_meds = {m.strip().lower() for m in medications if m.strip()}
    if len(unique_meds) >= 3:
        triggered.append("multiple_medications")

    # ── High-risk conditions (if not already clinical) ─────────────────────
    for code in HIGH_RISK_CONDITIONS:
        if medical_flags.get(code, False) and code not in triggered:
            triggered.append(code)

    # ── Medium-risk conditions ─────────────────────────────────────────────
    for code in MEDIUM_RISK_CONDITIONS:
        if medical_flags.get(code, False) and code not in triggered:
            triggered.append(code)

    # ── Determine final risk level ─────────────────────────────────────────
    if is_clinical:
        risk_level = "clinical_review_required"
    elif any(
        f in triggered
        for f in list(HIGH_RISK_CONDITIONS) + ["multiple_medications"]
    ):
        risk_level = "high"
    elif any(
        f in triggered
        for f in list(MEDIUM_RISK_CONDITIONS)
    ) or len(unique_meds) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return SafetyAssessment(
        risk_level=risk_level,
        flags_triggered=list(dict.fromkeys(triggered)),  # deduplicate, preserve order
        clinical_review_required=is_clinical,
    )
