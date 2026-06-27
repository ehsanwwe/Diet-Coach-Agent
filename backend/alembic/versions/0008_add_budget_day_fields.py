"""add_budget_day_fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-27

Additive changes only — safe for existing SQLite rows:
- nutrition_plan_days: add budget_tier, budget_guidance, shopping_notes
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("nutrition_plan_days", sa.Column("budget_tier", sa.String(20), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("budget_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("shopping_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("nutrition_plan_days", "shopping_notes")
    op.drop_column("nutrition_plan_days", "budget_guidance")
    op.drop_column("nutrition_plan_days", "budget_tier")
