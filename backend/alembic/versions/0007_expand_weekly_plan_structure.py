"""expand_weekly_plan_structure

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-27

Additive changes only — safe for existing SQLite users:
- nutrition_plan_days: add 23 new nullable columns for enriched day structure
- nutrition_plan_day_meals: add 12 new nullable columns for enriched meal structure
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nutrition_plan_days — day-level enriched fields
    op.add_column("nutrition_plan_days", sa.Column("diet_type", sa.String(50), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("diet_goal", sa.String(200), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("difficulty_level", sa.String(30), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("daily_calories", sa.Integer(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("daily_macros", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("day_type", sa.String(30), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("training_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("sleep_wake_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("wake_time", sa.String(10), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("sleep_time", sa.String(10), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("dinner_to_sleep_gap", sa.String(100), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("hydration_plan", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("drinks_plan", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("cheat_meal_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("allowed_foods", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("limited_foods", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("forbidden_foods", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("medical_warnings", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("restaurant_party_travel_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("supplements_vitamins_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("progress_tracking_guidance", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_days", sa.Column("adjustment_rules", sa.Text(), nullable=True))

    # nutrition_plan_day_meals — meal-level enriched fields
    op.add_column("nutrition_plan_day_meals", sa.Column("meal_slot", sa.String(50), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("meal_order", sa.Integer(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("time_window_start", sa.String(10), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("time_window_end", sa.String(10), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("calories_estimate", sa.Integer(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("protein_g", sa.Float(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("carbs_g", sa.Float(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("fat_g", sa.Float(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("food_items", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("workout_relation", sa.String(20), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("rest_day_note", sa.Text(), nullable=True))
    op.add_column("nutrition_plan_day_meals", sa.Column("drink_guidance", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("nutrition_plan_day_meals", "drink_guidance")
    op.drop_column("nutrition_plan_day_meals", "rest_day_note")
    op.drop_column("nutrition_plan_day_meals", "workout_relation")
    op.drop_column("nutrition_plan_day_meals", "food_items")
    op.drop_column("nutrition_plan_day_meals", "fat_g")
    op.drop_column("nutrition_plan_day_meals", "carbs_g")
    op.drop_column("nutrition_plan_day_meals", "protein_g")
    op.drop_column("nutrition_plan_day_meals", "calories_estimate")
    op.drop_column("nutrition_plan_day_meals", "time_window_end")
    op.drop_column("nutrition_plan_day_meals", "time_window_start")
    op.drop_column("nutrition_plan_day_meals", "meal_order")
    op.drop_column("nutrition_plan_day_meals", "meal_slot")

    op.drop_column("nutrition_plan_days", "adjustment_rules")
    op.drop_column("nutrition_plan_days", "progress_tracking_guidance")
    op.drop_column("nutrition_plan_days", "supplements_vitamins_guidance")
    op.drop_column("nutrition_plan_days", "restaurant_party_travel_guidance")
    op.drop_column("nutrition_plan_days", "medical_warnings")
    op.drop_column("nutrition_plan_days", "forbidden_foods")
    op.drop_column("nutrition_plan_days", "limited_foods")
    op.drop_column("nutrition_plan_days", "allowed_foods")
    op.drop_column("nutrition_plan_days", "cheat_meal_guidance")
    op.drop_column("nutrition_plan_days", "drinks_plan")
    op.drop_column("nutrition_plan_days", "hydration_plan")
    op.drop_column("nutrition_plan_days", "dinner_to_sleep_gap")
    op.drop_column("nutrition_plan_days", "sleep_time")
    op.drop_column("nutrition_plan_days", "wake_time")
    op.drop_column("nutrition_plan_days", "sleep_wake_guidance")
    op.drop_column("nutrition_plan_days", "training_guidance")
    op.drop_column("nutrition_plan_days", "day_type")
    op.drop_column("nutrition_plan_days", "daily_macros")
    op.drop_column("nutrition_plan_days", "daily_calories")
    op.drop_column("nutrition_plan_days", "difficulty_level")
    op.drop_column("nutrition_plan_days", "diet_goal")
    op.drop_column("nutrition_plan_days", "diet_type")
