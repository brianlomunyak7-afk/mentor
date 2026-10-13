"""create tutor answer logs

Revision ID: 0002_create_tutor_answer_logs
Revises: 0001_create_learner_profiles
Create Date: 2026-10-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_create_tutor_answer_logs"
down_revision: Union[str, Sequence[str], None] = "0001_create_learner_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutor_answer_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_message", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=150), nullable=False),
        sa.Column("sources_json", sa.Text(), nullable=False),
        sa.Column("reported_wrong", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("tutor_answer_logs")
