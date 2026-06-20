"""
SafetyGuardrailService: risk-level assessment from onboarding medical data.

Risk levels: low | medium | high | clinical_review_required

This service never gives medical prescriptions or dietary recommendations.
It only classifies risk and records the flags that triggered the classification.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re

# Conditions that always require clinical review before proceeding
CLINICAL_REVIEW_CONDITIONS: frozenset[str] = frozenset(
    {
        "kidney_disease",
        "pregnancy_breastfeeding",
        "pregnancy",
        "breastfeeding",
        "eating_disorder_history",
        "bariatric_surgery",
        "bariatric_surgery_history",
        "child_adolescent",
        "advanced_liver_disease",
        "cancer",
        "complex_heart_disease",
        "uncontrolled_thyroid_disorder",
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
    "gliclazide",
    "انسولین",
    "متفورمین",
    "گلیکلازید",
    "گلیبنکلامید",
    "گلیپیزید",
    "سیتاگلیپتین",
    "سماگلوتاید",
)

# High-risk conditions (not immediately clinical, but flagged as high)
HIGH_RISK_CONDITIONS: frozenset[str] = frozenset(
    {
        "diabetes",
        "liver_disease",
        "thyroid_issues",
        "heart_disease",
        "heart_failure",
        "sensitive_medications",
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
    "kidney",
    "kidney disease",
    "renal disease",
    "pregnancy",
    "pregnant",
    "breastfeeding",
    "breast feeding",
    "eating disorder",
    "anorexia",
    "bulimia",
    "binge purge",
    "bariatric",
    "gastric bypass",
    "cancer",
    "chemotherapy",
    "heart failure",
    "congestive heart failure",
    "complex heart",
    "advanced liver",
    "cirrhosis",
    "uncontrolled thyroid",
    "hyperthyroid uncontrolled",
    "hypothyroid uncontrolled",
    "under 1200 calories",
    "under 1000 calories",
    "800 calories",
    "starve myself",
    "stop eating",
    "کلیه",
    "بیماری کلیه",
    "بارداری",
    "باردار",
    "شیردهی",
    "اختلال خوردن",
    "بی اشتهایی عصبی",
    "پرخوری عصبی",
    "جراحی چاقی",
    "بای پس معده",
    "سرطان",
    "شیمی درمانی",
    "نارسایی قلبی",
    "بیماری قلبی پیچیده",
    "درد قفسه سینه",
    "خون در مدفوع",
    "کبد پیشرفته",
    "سیروز",
    "تیروئید کنترل نشده",
    "تیروئید کنترل‌نشده",
    "غش",
    "بیهوشی",
    "سرگیجه شدید",
    "کاهش وزن سریع",
    "کاهش وزن بی دلیل",
    "خودکشی",
    "خودآزاری",
    "کمتر از ۱۲۰۰ کالری",
    "کمتر از 1200 کالری",
    "۸۰۰ کالری",
    "800 کالری",
    "غذا نخورم",
)

CLINICAL_TEXT_FLAGS: dict[str, tuple[str, ...]] = {
    "kidney_disease": ("kidney disease", "renal disease", "بیماری کلیه", "نارسایی کلیه"),
    "pregnancy": ("pregnancy", "pregnant", "بارداری", "باردار"),
    "breastfeeding": ("breastfeeding", "breast feeding", "شیردهی"),
    "eating_disorder_history": ("eating disorder", "anorexia", "bulimia", "اختلال خوردن", "بی اشتهایی عصبی", "پرخوری عصبی"),
    "bariatric_surgery": ("bariatric", "gastric bypass", "جراحی چاقی", "بای پس معده"),
    "advanced_liver_disease": ("advanced liver", "cirrhosis", "کبد پیشرفته", "سیروز"),
    "cancer": ("cancer", "chemotherapy", "سرطان", "شیمی درمانی"),
    "complex_heart_disease": ("heart failure", "complex heart", "نارسایی قلبی", "بیماری قلبی پیچیده"),
    "uncontrolled_thyroid_disorder": ("uncontrolled thyroid", "تیروئید کنترل نشده", "تیروئید کنترل‌نشده"),
}

DANGEROUS_RESTRICTION_PATTERNS: tuple[str, ...] = (
    r"\b(?:[1-9]\d{2}|1[01]\d{2})\s*(?:kcal|calories|calorie)\b",
    r"\bunder\s+1200\s*(?:kcal|calories|calorie)\b",
    r"\b(?:starve myself|stop eating)\b",
    r"(?:کمتر از|زیر)\s*(?:۱۲۰۰|1200)\s*کالری",
    r"(?:۸۰۰|800)\s*کالری",
    r"غذا\s+نخورم",
)

SENSITIVE_MEDICATION_KEYWORDS: tuple[str, ...] = (
    "warfarin",
    "lithium",
    "digoxin",
    "steroid",
    "prednisone",
    "chemotherapy",
    "immunosuppressant",
    "وارفارین",
    "لیتیوم",
    "دیگوکسین",
    "پردنیزون",
    "کورتون",
    "شیمی درمانی",
    "داروی سرکوب ایمنی",
)


@dataclass
class SafetyAssessment:
    risk_level: str  # low | medium | high | clinical_review_required
    flags_triggered: list[str] = field(default_factory=list)
    clinical_review_required: bool = False


def _normalize_text(values: list[str]) -> str:
    return " ".join(v.strip().lower() for v in values if v and v.strip())


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


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
    free_text = _normalize_text(medications + warning_symptoms)

    # ── Child/adolescent ────────────────────────────────────────────────────
    if age is not None and age < 18:
        triggered.append("minor_user")
        is_clinical = True

    # ── Clinical review conditions ─────────────────────────────────────────
    for code in CLINICAL_REVIEW_CONDITIONS:
        if medical_flags.get(code, False):
            triggered.append(code)
            is_clinical = True

    for code, keywords in CLINICAL_TEXT_FLAGS.items():
        if _contains_any(free_text, keywords):
            triggered.append(code)
            is_clinical = True

    # ── Diabetes + any diabetes medication → clinical ───────────────────────
    if medical_flags.get("diabetes", False):
        if "diabetes" not in triggered:
            triggered.append("diabetes")
        med_text = _normalize_text(medications)
        for keyword in DIABETES_MEDICATION_KEYWORDS:
            if keyword.lower() in med_text:
                triggered.append("diabetes_with_medication")
                is_clinical = True
                break

    if _contains_any(_normalize_text(medications), SENSITIVE_MEDICATION_KEYWORDS):
        triggered.append("sensitive_medications")

    # ── Warning symptoms ───────────────────────────────────────────────────
    symptoms_text = _normalize_text(warning_symptoms)
    for keyword in WARNING_SYMPTOM_KEYWORDS:
        if keyword.lower() in symptoms_text:
            triggered.append(f"symptom:{keyword.replace(' ', '_')}")
            is_clinical = True

    for pattern in DANGEROUS_RESTRICTION_PATTERNS:
        if re.search(pattern, symptoms_text, flags=re.IGNORECASE):
            triggered.append("dangerous_calorie_restriction")
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
