from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    settings = get_settings()
    return {
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_pre_ping": True,
    }


engine = create_engine(
    get_settings().database_url,
    **_engine_kwargs(get_settings().database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
