"""create resources

Revision ID: 0004_create_resources
Revises: 0003_create_learning_plans
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_create_resources"
down_revision: Union[str, Sequence[str], None] = "0003_create_learning_plans"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("credibility_score", sa.Float(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_resources_lesson_id", "resources", ["lesson_id"])


def downgrade() -> None:
    op.drop_index("ix_resources_lesson_id", table_name="resources")
    op.drop_table("resources")
