"""add_nutrition_calendar

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-06

Adds multilingual rolling meal plan calendar tables:
  - nutrition_plan_calendars
  - nutrition_plan_days
  - nutrition_plan_day_meals
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nutrition_plan_calendars",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(5), nullable=False, server_default="fa"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_calendar_user_id", "nutrition_plan_calendars", ["user_id"])
    op.create_index("ix_calendar_locale", "nutrition_plan_calendars", ["locale"])
    op.create_index(
        "ix_calendar_user_locale", "nutrition_plan_calendars", ["user_id", "locale"]
    )

    op.create_table(
        "nutrition_plan_days",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "calendar_id",
            sa.String(36),
            sa.ForeignKey("nutrition_plan_calendars.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(5), nullable=False, server_default="fa"),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("hydration_goal", sa.String(300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "plan_date", "locale", name="uq_plan_day_user_date_locale"),
    )
    op.create_index("ix_plan_day_calendar_id", "nutrition_plan_days", ["calendar_id"])
    op.create_index("ix_plan_day_user_id", "nutrition_plan_days", ["user_id"])
    op.create_index("ix_plan_day_locale", "nutrition_plan_days", ["locale"])
    op.create_index("ix_plan_day_plan_date", "nutrition_plan_days", ["plan_date"])
    op.create_index(
        "ix_plan_day_user_locale_date",
        "nutrition_plan_days",
        ["user_id", "locale", "plan_date"],
    )

    op.create_table(
        "nutrition_plan_day_meals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "plan_day_id",
            sa.String(36),
            sa.ForeignKey("nutrition_plan_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(5), nullable=False, server_default="fa"),
        sa.Column("meal_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("portion_guidance", sa.String(500), nullable=True),
        sa.Column("alternatives", sa.Text(), nullable=True),
        sa.Column("preparation_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_plan_day_meal_plan_day_id", "nutrition_plan_day_meals", ["plan_day_id"]
    )


def downgrade() -> None:
    op.drop_table("nutrition_plan_day_meals")
    op.drop_table("nutrition_plan_days")
    op.drop_table("nutrition_plan_calendars")
