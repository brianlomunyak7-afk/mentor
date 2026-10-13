"""create learning plans and lessons

Revision ID: 0003_create_learning_plans
Revises: 0002_create_tutor_answer_logs
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_create_learning_plans"
down_revision: Union[str, Sequence[str], None] = "0002_create_tutor_answer_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("module_number", sa.Integer(), nullable=False),
        sa.Column("lesson_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("examples_json", sa.Text(), nullable=False),
        sa.Column("practice_task", sa.Text(), nullable=False),
        sa.Column("quiz_json", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_lessons_plan_id", "lessons", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_lessons_plan_id", table_name="lessons")
    op.drop_table("lessons")
    op.drop_table("learning_plans")
