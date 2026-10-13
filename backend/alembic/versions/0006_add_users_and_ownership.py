"""add users and ownership columns

Revision ID: 0006_add_users_and_ownership
Revises: 0005_add_notes_bookmarks_quizzes
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_add_users_and_ownership"
down_revision: Union[str, Sequence[str], None] = "0005_add_notes_bookmarks_quizzes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OWNED_TABLES = (
    "learner_profiles",
    "tutor_answer_logs",
    "learning_plans",
    "lessons",
    "resources",
    "notes",
    "bookmarks",
    "quiz_attempts",
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", sa.Integer()),
            sa.column("email", sa.String()),
            sa.column("role", sa.String()),
            sa.column("is_active", sa.Boolean()),
        ),
        [{"id": 1, "email": "demo@tutorai.local", "role": "learner", "is_active": True}],
    )
    for table_name in OWNED_TABLES:
        op.add_column(table_name, sa.Column("user_id", sa.Integer(), nullable=True))
        op.create_index(f"ix_{table_name}_user_id", table_name, ["user_id"])
        op.execute(f"UPDATE {table_name} SET user_id = 1 WHERE user_id IS NULL")


def downgrade() -> None:
    for table_name in reversed(OWNED_TABLES):
        op.drop_index(f"ix_{table_name}_user_id", table_name=table_name)
        op.drop_column(table_name, "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
