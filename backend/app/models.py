from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    learning_topic: Mapped[str | None] = mapped_column(String(200))
    motivation: Mapped[str | None] = mapped_column(Text)
    goal: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[str | None] = mapped_column(String(100))
    current_level: Mapped[str | None] = mapped_column(String(20))
    daily_minutes: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(50), default="English")
    device_limits: Mapped[str | None] = mapped_column(Text)
    internet_limits: Mapped[str | None] = mapped_column(Text)
    preference_data: Mapped[str] = mapped_column(Text, default="{}")
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
