"""Diet protocol safety checks — blocks dangerous protocol+condition combos."""
from __future__ import annotations

from dataclasses import dataclass

_BLOCKED_COMBOS: dict[str, list[str]] = {
    "keto": [
        "diabetes",
        "kidney_disease",
        "eating_disorder_history",
        "pregnancy",
        "pregnancy_breastfeeding",
    ],
    "intermittent_fasting": [
        "diabetes",
        "eating_disorder_history",
        "pregnancy",
        "pregnancy_breastfeeding",
        "child_adolescent",
    ],
    "calorie_deficit": [
        "eating_disorder_history",
        "pregnancy",
        "pregnancy_breastfeeding",
    ],
}

_SAFER_ALTERNATIVES: dict[str, str] = {
    "keto": "low_carb",
    "intermittent_fasting": "calorie_deficit",
    "calorie_deficit": "mediterranean",
}

_AGGRESSIVE_PROTOCOLS = {"keto", "intermittent_fasting"}


@dataclass
class ProtocolSafetyResult:
    blocked: bool
    reason: str | None
    safer_protocol: str | None


def check_protocol_safety(protocol: str, ctx) -> ProtocolSafetyResult:
    """Return safety result for a diet protocol given the user's medical context.

    Low-risk users with no flags are never blocked.
    """
    active_flags: list[str] = list(ctx.active_medical_flags or [])

    # Block aggressive protocols when a clinician review is flagged
    if protocol in _AGGRESSIVE_PROTOCOLS and getattr(ctx, "clinical_review_required", False):
        return ProtocolSafetyResult(
            blocked=True,
            reason="clinical_review_required",
            safer_protocol=_SAFER_ALTERNATIVES.get(protocol),
        )

    # Block fasting/deficit for users with a binge-eating history
    if protocol in {"intermittent_fasting", "calorie_deficit"} and getattr(ctx, "binge_history", False):
        return ProtocolSafetyResult(
            blocked=True,
            reason="binge_history",
            safer_protocol=_SAFER_ALTERNATIVES.get(protocol),
        )

    # Block specific flag+protocol combinations
    blocked_flags = _BLOCKED_COMBOS.get(protocol, [])
    for flag in active_flags:
        if flag in blocked_flags:
            return ProtocolSafetyResult(
                blocked=True,
                reason=flag,
                safer_protocol=_SAFER_ALTERNATIVES.get(protocol),
            )

    return ProtocolSafetyResult(blocked=False, reason=None, safer_protocol=None)
