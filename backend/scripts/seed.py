import argparse

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User


def seed() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admin-email", default="admin@tutorai.local")
    parser.add_argument("--demo-email", default="demo@tutorai.local")
    args = parser.parse_args()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == args.admin_email)) is None:
            db.add(User(email=args.admin_email, role="admin", is_active=True))
        if db.scalar(select(User).where(User.email == args.demo_email)) is None:
            db.add(User(email=args.demo_email, role="learner", is_active=True))
        db.commit()
    print(f"Seeded admin={args.admin_email} learner={args.demo_email}")


if __name__ == "__main__":
    seed()
