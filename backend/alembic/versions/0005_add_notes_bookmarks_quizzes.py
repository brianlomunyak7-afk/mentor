"""add notes bookmarks and quizzes

Revision ID: 0005_add_notes_bookmarks_quizzes
Revises: 0004_create_resources
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_add_notes_bookmarks_quizzes"
down_revision: Union[str, Sequence[str], None] = "0004_create_resources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("lesson_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_notes_lesson_id", "notes", ["lesson_id"])
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_quiz_attempts_lesson_id", "quiz_attempts", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_quiz_attempts_lesson_id", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_table("bookmarks")
    op.drop_index("ix_notes_lesson_id", table_name="notes")
    op.drop_table("notes")
