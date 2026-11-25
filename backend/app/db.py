"""Database engine and SQLAlchemy session dependency."""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all ORM models."""


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hanbowei.db")
_engine_options = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
