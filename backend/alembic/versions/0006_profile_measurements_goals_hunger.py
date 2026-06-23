"""profile_measurements_goals_hunger

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-23

Additive changes only — safe for existing SQLite users:
- user_profiles: add wrist_cm, thigh_cm (nullable Float)
- behavior_profiles: add hunger_patterns (nullable Text JSON list)
  Old hunger_pattern (String 50) is preserved for backward compat.
- nutrition_goals: add goal_types_json (nullable Text JSON list)
  Old goal_type (String 50) is preserved for backward compat.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("wrist_cm", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("thigh_cm", sa.Float(), nullable=True))
    op.add_column("behavior_profiles", sa.Column("hunger_patterns", sa.Text(), nullable=True))
    op.add_column("nutrition_goals", sa.Column("goal_types_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("nutrition_goals", "goal_types_json")
    op.drop_column("behavior_profiles", "hunger_patterns")
    op.drop_column("user_profiles", "thigh_cm")
    op.drop_column("user_profiles", "wrist_cm")
