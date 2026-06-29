"""
Tests for preference_extractor — food dislike/like extraction from free text
and plan violation scanning.
"""
from __future__ import annotations

import pytest

from app.services.preference_extractor import (
    extract_food_preferences,
    find_dislike_violations,
    normalize_for_compare,
)


# ── normalize_for_compare ─────────────────────────────────────────────────────

def test_normalize_strips_halfspace():
    assert normalize_for_compare("کوکو‌سبزی") == normalize_for_compare("کوکو سبزی")


def test_normalize_arabic_ya():
    assert normalize_for_compare("كوكو سبزي") == normalize_for_compare("کوکو سبزی")


def test_normalize_arabic_kaf():
    assert normalize_for_compare("ك") == normalize_for_compare("ک")


# ── extract_food_preferences — dislikes ───────────────────────────────────────

def test_basic_persian_dislike_bade_miad():
    dislikes, likes = extract_food_preferences("من از کوکو سبزی بدم میاد")
    assert "کوکو سبزی" in dislikes
    assert likes == []


def test_persian_dislike_doost_nadaram():
    dislikes, _ = extract_food_preferences("ماهی دوست ندارم")
    assert any("ماهی" in d for d in dislikes)


def test_persian_dislike_nemikharam():
    dislikes, _ = extract_food_preferences("جگر نمیخورم")
    assert any("جگر" in d for d in dislikes)


def test_persian_dislike_halam_bad():
    dislikes, _ = extract_food_preferences("حالم از میگو بد میشه")
    assert any("میگو" in d for d in dislikes)


def test_english_dislike():
    dislikes, _ = extract_food_preferences("I don't like fish")
    assert any("fish" in d.lower() for d in dislikes)


def test_english_dislike_hate():
    dislikes, _ = extract_food_preferences("I hate liver")
    assert any("liver" in d.lower() for d in dislikes)


# ── extract_food_preferences — likes ─────────────────────────────────────────

def test_persian_like_doost_daram():
    _, likes = extract_food_preferences("مرغ دوست دارم")
    assert any("مرغ" in li for li in likes)


def test_english_like():
    _, likes = extract_food_preferences("I love chicken")
    assert any("chicken" in li.lower() for li in likes)


# ── Negative preference wins over likes ───────────────────────────────────────

def test_dislike_wins_over_like_in_same_text():
    text = "کوکو سبزی دوست دارم ولی حالم از کوکو سبزی بد میشه"
    dislikes, likes = extract_food_preferences(text)
    norms = {normalize_for_compare(d) for d in dislikes}
    assert normalize_for_compare("کوکو سبزی") in norms
    # Should NOT appear in likes
    for li in likes:
        assert normalize_for_compare(li) != normalize_for_compare("کوکو سبزی")


# ── Normalization variants ────────────────────────────────────────────────────

def test_arabic_variant_matches_persian():
    """Arabic-script variant of کوکو سبزی should match the normalized form."""
    dislikes, _ = extract_food_preferences("از كوكو سبزي بدم میاد")
    norms = {normalize_for_compare(d) for d in dislikes}
    assert normalize_for_compare("کوکو سبزی") in norms


def test_halfspace_variant_matches():
    dislikes, _ = extract_food_preferences("از کوکو‌سبزی بدم میاد")
    norms = {normalize_for_compare(d) for d in dislikes}
    assert normalize_for_compare("کوکوسبزی") in norms or normalize_for_compare("کوکو سبزی") in norms


# ── find_dislike_violations ───────────────────────────────────────────────────

def test_no_violations_when_no_dislikes():
    plan = {"days": [{"meals": [{"title": "کوکو سبزی", "alternatives": ["ماهی"]}]}]}
    assert find_dislike_violations(plan, []) == []


def test_violation_found_in_meal_title():
    plan = {"days": [{"meals": [{"title": "کوکو سبزی"}]}]}
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert "کوکو سبزی" in violations


def test_violation_found_in_alternatives():
    plan = {"days": [{"meals": [{"alternatives": ["کوکو سبزی", "سالاد"]}]}]}
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert "کوکو سبزی" in violations


def test_violation_found_in_shopping_notes():
    plan = {"days": [{"shopping_notes": "کوکو سبزی برای ناهار فراموش نشه"}]}
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert "کوکو سبزی" in violations


def test_no_violation_when_not_present():
    plan = {"days": [{"meals": [{"title": "مرغ و سبزیجات", "alternatives": ["ماهی"]}]}]}
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert violations == []


def test_violation_recursive_nested():
    plan = {
        "days": [
            {
                "cheat_meal_guidance": "میتونی کوکو سبزی بخوری",
                "meals": [{"food_items": [{"name": "کوکو سبزی"}]}],
            }
        ]
    }
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert "کوکو سبزی" in violations


def test_arabic_script_variant_caught_by_validator():
    """Normalized comparison should catch arabic-script variant inside the plan."""
    plan = {"days": [{"meals": [{"title": "كوكو سبزي"}]}]}
    violations = find_dislike_violations(plan, ["کوکو سبزی"])
    assert len(violations) > 0


def test_favorites_do_not_override_dislikes_in_merging():
    """
    Integration-style test: merge_food_likes should not add a food that is already
    in the disliked list.
    """
    from unittest.mock import MagicMock
    import json as _json
    from app.repositories.onboarding_repository import merge_food_likes

    fp = MagicMock()
    fp.disliked_foods = _json.dumps(["کوکو سبزی"])
    fp.favorite_foods = _json.dumps([])

    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = fp

    # Should not raise and should not add کوکو سبزی to favorites
    merge_food_likes(db, "user-1", ["کوکو سبزی"])
    saved = _json.loads(fp.favorite_foods)
    assert "کوکو سبزی" not in saved
