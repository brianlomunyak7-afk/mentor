"""create learner profiles

Revision ID: 0001_create_learner_profiles
Revises:
Create Date: 2026-10-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_learner_profiles"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("learning_topic", sa.String(length=200)),
        sa.Column("motivation", sa.Text()),
        sa.Column("goal", sa.Text()),
        sa.Column("deadline", sa.String(length=100)),
        sa.Column("current_level", sa.String(length=20)),
        sa.Column("daily_minutes", sa.Integer()),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column("device_limits", sa.Text()),
        sa.Column("internet_limits", sa.Text()),
        sa.Column("preference_data", sa.Text(), nullable=False),
        sa.Column("onboarding_step", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("learner_profiles")
