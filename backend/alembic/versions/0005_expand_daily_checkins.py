"""expand_daily_checkins

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-20

Adds optional daily check-in signals for richer nutrition memory.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("daily_checkins", schema=None) as batch_op:
        batch_op.add_column(sa.Column("waist_cm", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("hunger_level_1_10", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("sleep_quality", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("energy_level", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cravings", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("craving_type", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("eating_location", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("planned_eating_out", sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column("adherence_level", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("symptoms", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("daily_checkins", schema=None) as batch_op:
        batch_op.drop_column("symptoms")
        batch_op.drop_column("adherence_level")
        batch_op.drop_column("planned_eating_out")
        batch_op.drop_column("eating_location")
        batch_op.drop_column("craving_type")
        batch_op.drop_column("cravings")
        batch_op.drop_column("energy_level")
        batch_op.drop_column("sleep_quality")
        batch_op.drop_column("hunger_level_1_10")
        batch_op.drop_column("waist_cm")
