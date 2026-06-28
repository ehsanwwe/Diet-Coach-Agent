"""
SQL safety layer for the query_user_nutrition_data agent tool.

Conservative by design: prefer rejection over risky acceptance.
No external SQL parser dependency — pure regex + structural checks.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

# ─── Whitelist ────────────────────────────────────────────────────────────────

ALLOWED_TABLES: frozenset[str] = frozenset({
    # Onboarding / profile
    "user_profiles",
    "user_medical_flags",
    "medical_conditions",
    "medications",
    "allergies",
    "lifestyle_profiles",
    "food_preferences",
    "behavior_profiles",
    # Goals & risk
    "nutrition_goals",
    "nutrition_risk_assessments",
    # Plans
    "nutrition_plans",
    "nutrition_plan_meals",
    # Calendar
    "nutrition_plan_calendars",
    "nutrition_plan_days",
    "nutrition_plan_day_meals",
    # Logs & progress
    "meal_entries",
    "daily_checkins",
    "progress_entries",
    "weekly_reports",
    # Preferences
    "user_language_preferences",
})

# Tables explicitly blocked (defense-in-depth on top of whitelist)
_BLOCKED_TABLES: frozenset[str] = frozenset({
    "users",
    "auth_otps",
    "token_blocklist",
    "audit_logs",
})

# Write / DDL / dangerous statement keywords — word-boundary matched
_BLOCKED_STATEMENT_KEYWORDS: tuple[str, ...] = (
    "insert", "update", "delete", "drop", "alter", "create", "replace",
    "truncate", "vacuum", "attach", "detach", "pragma", "exec", "merge", "upsert",
)

# Set operations that could bypass per-user scoping
_BLOCKED_SET_OPERATIONS: tuple[str, ...] = ("union", "intersect", "except")

# SQLite internal metadata tables
_BLOCKED_META_TABLES: tuple[str, ...] = (
    "sqlite_master", "sqlite_schema", "sqlite_temp_master", "information_schema",
)

# Sensitive column name patterns — never returned even if table is whitelisted
_BLOCKED_COLUMN_PATTERNS: tuple[str, ...] = (
    "password", "hashed_password", "otp_code", "token",
    "refresh_token", "reset_token", "api_key", "secret",
    "jti", "phone", "attempt_count", "invalidated_at",
)

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100
_MAX_STRING_LEN = 500
_MAX_ROWS = 100


# ─── Result type ──────────────────────────────────────────────────────────────

@dataclass
class SafeSqlResult:
    valid: bool
    error: str | None = None
    normalized_sql: str | None = None


# ─── Individual checks ────────────────────────────────────────────────────────

def _check_no_comments(sql: str) -> str | None:
    if "--" in sql:
        return "SQL comments (--) are not allowed"
    if re.search(r"/\*", sql):
        return "SQL block comments are not allowed"
    return None


def _check_no_multiple_statements(sql: str) -> str | None:
    # Strip a single harmless trailing semicolon, then reject any remaining ';'
    stripped = sql.rstrip().rstrip(";").rstrip()
    if ";" in stripped:
        return "Multiple SQL statements are not allowed"
    return None


def _check_starts_with_select(sql: str) -> str | None:
    upper = sql.strip().upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return "Only SELECT (or WITH ... SELECT) queries are allowed"
    return None


def _check_blocked_keywords(sql: str) -> str | None:
    lower = sql.lower()
    for kw in _BLOCKED_STATEMENT_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            return f"Blocked SQL keyword: {kw.upper()}"
    return None


def _check_no_set_operations(sql: str) -> str | None:
    lower = sql.lower()
    for op in _BLOCKED_SET_OPERATIONS:
        if re.search(r"\b" + re.escape(op) + r"\b", lower):
            return f"SQL set operation {op.upper()} is not allowed"
    return None


def _check_no_meta_tables(sql: str) -> str | None:
    lower = sql.lower()
    for meta in _BLOCKED_META_TABLES:
        if re.search(r"\b" + re.escape(meta) + r"\b", lower):
            return f"Access to system table '{meta}' is not allowed"
    return None


def _check_no_blocked_tables(sql: str) -> str | None:
    lower = sql.lower()
    for table in _BLOCKED_TABLES:
        if re.search(r"\b" + re.escape(table) + r"\b", lower):
            return f"Access to table '{table}' is not allowed"
    return None


def _extract_cte_names(sql: str) -> set[str]:
    """Extract alias names defined in WITH clause so they don't fail table checks."""
    lower = sql.lower()
    names: set[str] = set()
    # WITH name AS ( ...
    for m in re.finditer(r"\bwith\b\s+(\w+)\s+as\s*\(", lower):
        names.add(m.group(1))
    # , name AS (  — subsequent CTEs in the same WITH
    for m in re.finditer(r",\s*(\w+)\s+as\s*\(", lower):
        names.add(m.group(1))
    return names


def _extract_table_names(sql: str) -> set[str]:
    """Extract table names from FROM and JOIN clauses (regex approximation)."""
    lower = sql.lower()
    return {m.group(1).lower() for m in re.finditer(r"(?:from|join)\s+([a-z_][a-z0-9_]*)", lower)}


def _check_allowed_tables(sql: str) -> str | None:
    tables = _extract_table_names(sql)
    cte_names = _extract_cte_names(sql)
    real_tables = tables - cte_names

    if not real_tables:
        return "Query must reference at least one allowed table"

    for table in real_tables:
        if table in _BLOCKED_TABLES:
            return f"Access to table '{table}' is not allowed"
        if table not in ALLOWED_TABLES:
            return f"Table '{table}' is not in the allowed list"
    return None


def _check_no_sensitive_columns(sql: str) -> str | None:
    lower = sql.lower()
    for col in _BLOCKED_COLUMN_PATTERNS:
        if re.search(r"\b" + re.escape(col) + r"\b", lower):
            return f"Access to sensitive field '{col}' is not allowed"
    return None


def _check_user_id_binding(sql: str) -> str | None:
    if ":user_id" not in sql:
        return "Query must use :user_id parameter to scope results to the current user"
    return None


def _check_no_literal_user_id(sql: str) -> str | None:
    """Reject UUID literals that might hard-code a specific user."""
    uuid_re = re.compile(
        r"['\"]?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}['\"]?",
        re.IGNORECASE,
    )
    if uuid_re.search(sql):
        return "Literal user IDs are not allowed; use :user_id parameter only"
    return None


# ─── LIMIT enforcement ────────────────────────────────────────────────────────

def _ensure_limit(
    sql: str,
    default_limit: int = _DEFAULT_LIMIT,
    max_limit: int = _MAX_LIMIT,
) -> str:
    """Append or cap the LIMIT clause. Strips trailing semicolons first."""
    sql = sql.rstrip().rstrip(";").rstrip()
    limit_re = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
    match = limit_re.search(sql)
    if not match:
        return f"{sql} LIMIT {default_limit}"
    current = int(match.group(1))
    if current > max_limit:
        return limit_re.sub(f"LIMIT {max_limit}", sql)
    return sql


# ─── Master validation ────────────────────────────────────────────────────────

def validate_readonly_user_sql(sql: str) -> SafeSqlResult:
    """
    Run all safety checks against a raw SQL string.
    Returns SafeSqlResult(valid=True, normalized_sql=...) on success,
    or SafeSqlResult(valid=False, error=...) on first failure.
    """
    if not sql or not sql.strip():
        return SafeSqlResult(valid=False, error="Empty query")

    # Comments first: they can hide blocked keywords
    err = _check_no_comments(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # Multiple statements
    err = _check_no_multiple_statements(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # Must start with SELECT or WITH
    err = _check_starts_with_select(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # No write/DDL keywords
    err = _check_blocked_keywords(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # No UNION / INTERSECT / EXCEPT
    err = _check_no_set_operations(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # No SQLite metadata tables
    err = _check_no_meta_tables(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # Explicit blocked-table defense-in-depth
    err = _check_no_blocked_tables(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # All referenced tables must be whitelisted
    err = _check_allowed_tables(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # No sensitive columns
    err = _check_no_sensitive_columns(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # Must use :user_id binding
    err = _check_user_id_binding(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    # No literal UUID user IDs
    err = _check_no_literal_user_id(sql)
    if err:
        return SafeSqlResult(valid=False, error=err)

    normalized = _ensure_limit(sql)
    return SafeSqlResult(valid=True, normalized_sql=normalized)


# ─── Result serialization ─────────────────────────────────────────────────────

def _safe_value(v: Any) -> Any:
    """Convert a DB value to a JSON-serializable, safely bounded type."""
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, str) and len(v) > _MAX_STRING_LEN:
        return v[:_MAX_STRING_LEN] + "…"
    return v


# ─── Execution ────────────────────────────────────────────────────────────────

def execute_safe_user_query(
    db: Any,
    sql: str,
    user_id: str,
    question: str = "",
) -> dict:
    """
    Validate and execute a user-scoped read-only query.

    On success returns:
        {"success": True, "question": str, "row_count": int,
         "columns": [...], "rows": [...], "truncated": bool}

    On validation or execution failure returns:
        {"success": False, "error": "unsafe_or_invalid_query"}

    Raw SQL errors are never surfaced in the return value.
    """
    from sqlalchemy import text

    result = validate_readonly_user_sql(sql)
    if not result.valid:
        logger.warning(
            "SQL validation failed: %s | query_preview=%.150s",
            result.error, sql,
        )
        return {"success": False, "error": "unsafe_or_invalid_query"}

    try:
        cursor = db.execute(text(result.normalized_sql), {"user_id": user_id})
        columns: list[str] = list(cursor.keys())
        # Fetch one extra row to detect truncation without reading the whole table
        raw_rows = cursor.fetchmany(_MAX_ROWS + 1)
        truncated = len(raw_rows) > _MAX_ROWS
        rows = raw_rows[:_MAX_ROWS]

        formatted = [
            {col: _safe_value(val) for col, val in zip(columns, row)}
            for row in rows
        ]

        return {
            "success": True,
            "question": question,
            "row_count": len(formatted),
            "columns": columns,
            "rows": formatted,
            "truncated": truncated,
        }

    except Exception as exc:
        # Never expose internal error details to the LLM or user
        logger.warning("Safe query execution error: %s", exc)
        return {"success": False, "error": "query_execution_failed"}
