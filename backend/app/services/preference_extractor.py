"""
preference_extractor.py — lightweight food preference extraction from free text.

Detects dislike/like expressions in Persian, Arabic, and English using
deterministic regex patterns, then normalizes food names for storage.
No LLM call — runs synchronously as a side-effect of every chat message.
"""
from __future__ import annotations

import re


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_persian(text: str) -> str:
    """Normalize Arabic/Persian character variants and remove zero-width non-joiner."""
    text = text.replace('‌', '')   # ZWNJ / half-space
    text = text.replace('​', '')   # zero-width space
    text = text.replace('ي', 'ی')       # Arabic ya → Persian ya
    text = text.replace('ك', 'ک')       # Arabic kaf → Persian kaf
    text = text.replace('ة', 'ه')       # Arabic ta marbuta → ha
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_for_compare(food: str) -> str:
    """Return a collapsed lowercase form for deduplication comparison."""
    return normalize_persian(food).lower().replace(' ', '')


# ── Patterns ──────────────────────────────────────────────────────────────────

# Each pattern must have exactly one capturing group containing the food name.
# Persian patterns first, then English fallback.
_DISLIKE_PATTERNS: list[re.Pattern[str]] = [
    # "از X بدم میاد" and variants
    re.compile(r'از\s+(.+?)\s+بدم\s+می[‌\s]?آید', re.UNICODE),
    re.compile(r'از\s+(.+?)\s+بدم\s+میاد', re.UNICODE),
    re.compile(r'از\s+(.+?)\s+بدم\s+میاید', re.UNICODE),
    # "X دوست ندارم" / "X رو دوست ندارم"
    re.compile(r'(.+?)\s+(?:رو\s+)?دوست\s+ندارم', re.UNICODE),
    # "X نمی‌خورم" / "X نمیخورم"
    re.compile(r'(.+?)\s+نمی[‌\s]?خورم', re.UNICODE),
    # "حالم از X بد میشه" / "حالم از X به هم میخوره"
    re.compile(r'حالم\s+از\s+(.+?)\s+بد\s+میشه', re.UNICODE),
    re.compile(r'حالم\s+از\s+(.+?)\s+به\s+هم\s+می[‌\s]?خوره', re.UNICODE),
    # "با X مشکل دارم"
    re.compile(r'با\s+(.+?)\s+مشکل\s+دارم', re.UNICODE),
    # "X نمی‌خوام" / "X نمیخوام"
    re.compile(r'(.+?)\s+نمی[‌\s]?خوام', re.UNICODE),
    # "X نباشه" / "X نباشد"
    re.compile(r'(.+?)\s+نباشه?', re.UNICODE),
    # English patterns
    re.compile(
        r"i\s+(?:don['']t|do\s+not|hate|dislike|avoid|can['']t\s+stand|cannot\s+stand)\s+(.+?)(?:[.,!؟?]|$)",
        re.IGNORECASE | re.UNICODE,
    ),
    re.compile(r"not\s+a\s+fan\s+of\s+(.+?)(?:[.,!؟?]|$)", re.IGNORECASE | re.UNICODE),
    re.compile(r"(.+?)\s+(?:is|are)\s+(?:gross|disgusting|awful|terrible)", re.IGNORECASE | re.UNICODE),
]

_LIKE_PATTERNS: list[re.Pattern[str]] = [
    # "X دوست دارم" / "X رو دوست دارم"
    re.compile(r'(.+?)\s+(?:رو\s+)?دوست\s+دارم', re.UNICODE),
    # "به X علاقه دارم"
    re.compile(r'به\s+(.+?)\s+علاقه\s+دارم', re.UNICODE),
    # "X رو ترجیح میدم"
    re.compile(r'(.+?)\s+(?:رو\s+)?ترجیح\s+میدم', re.UNICODE),
    # "از X خوشم میاد"
    re.compile(r'از\s+(.+?)\s+خوشم\s+میاد', re.UNICODE),
    # English
    re.compile(
        r"i\s+(?:love|like|enjoy|prefer|adore)\s+(.+?)(?:[.,!؟?]|$)",
        re.IGNORECASE | re.UNICODE,
    ),
]

# Tokens that are almost certainly not food names
_REJECTED_TOKENS: frozenset[str] = frozenset({
    'من', 'تو', 'او', 'اون', 'ما', 'شما', 'اونا', 'آنها',
    'هیچ', 'این', 'اون', 'آن', 'همه', 'بعضی',
    'i', 'me', 'you', 'we', 'they', 'it', 'he', 'she',
    'this', 'that', 'these', 'those', 'some', 'any', 'all',
    'غذا', 'خوراک', 'وعده', 'مواد', 'چیز',
})


def _clean_food_name(raw: str) -> str | None:
    """Strip function words and validate the candidate food name."""
    name = normalize_persian(raw)
    # Strip leading/trailing punctuation
    name = name.strip('.,!؟? "\'«»')
    # Remove leading Persian particles
    name = re.sub(r'^(?:به|از|با|رو|را|که)\s+', '', name, flags=re.UNICODE)
    # Remove trailing Persian particles
    name = re.sub(r'\s+(?:رو|را|هم|هم|هم)$', '', name, flags=re.UNICODE)
    name = name.strip()
    if not name or len(name) < 2 or len(name) > 60:
        return None
    if normalize_for_compare(name) in _REJECTED_TOKENS:
        return None
    return name


# ── Public API ────────────────────────────────────────────────────────────────

def find_dislike_violations(plan_data: object, disliked_foods: list[str]) -> list[str]:
    """
    Recursively scan all string values in plan_data for any disliked food name.
    Returns a list of violation strings (food names found) for logging.
    Uses normalized comparison so variants like كوكو سبزي match کوکو سبزی.
    """
    if not disliked_foods:
        return []

    norm_dislikes = [(d, normalize_for_compare(d)) for d in disliked_foods]
    violations: list[str] = []

    def _scan(node: object) -> None:
        if isinstance(node, str):
            node_norm = normalize_for_compare(node)
            for food, food_norm in norm_dislikes:
                if food_norm and food_norm in node_norm:
                    violations.append(food)
        elif isinstance(node, dict):
            for v in node.values():
                _scan(v)
        elif isinstance(node, list):
            for item in node:
                _scan(item)

    _scan(plan_data)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def extract_food_preferences(text: str) -> tuple[list[str], list[str]]:
    """
    Return (dislikes, likes) lists extracted from free-text message.

    Normalization is applied before matching.
    Negative preferences win: a food that matches both dislike AND like patterns
    is placed only in dislikes, not likes.
    """
    norm = normalize_persian(text)

    dislikes: list[str] = []
    seen_dislike: set[str] = set()
    for pat in _DISLIKE_PATTERNS:
        for m in pat.finditer(norm):
            food = _clean_food_name(m.group(1))
            if food is None:
                continue
            key = normalize_for_compare(food)
            if key not in seen_dislike:
                seen_dislike.add(key)
                dislikes.append(food)

    likes: list[str] = []
    seen_like: set[str] = set()
    for pat in _LIKE_PATTERNS:
        for m in pat.finditer(norm):
            food = _clean_food_name(m.group(1))
            if food is None:
                continue
            key = normalize_for_compare(food)
            if key in seen_dislike:
                continue  # Negative preference wins
            if key not in seen_like:
                seen_like.add(key)
                likes.append(food)

    return dislikes, likes
