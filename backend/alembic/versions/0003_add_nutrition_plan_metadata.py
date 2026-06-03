"""add_nutrition_plan_metadata

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03

Adds plan_metadata (Text, nullable) to nutrition_plans.
Stores JSON with daily_guidelines, warnings, and provider info.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("nutrition_plans", schema=None) as batch_op:
        batch_op.add_column(sa.Column("plan_metadata", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("nutrition_plans", schema=None) as batch_op:
        batch_op.drop_column("plan_metadata")
