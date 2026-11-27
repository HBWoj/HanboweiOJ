import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Base
from app.models import User, UserSession


@pytest.fixture
def session():
    """Create an isolated database for session-model tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def add_user(session: Session) -> User:
    user = User(
        username="student001",
        display_name="Test Student",
        password_hash="test-hash-not-used-for-authentication",
    )
    session.add(user)
    session.commit()
    return user


def add_session(
    session: Session,
    user_id: uuid.UUID,
    token_hash: str = "a" * 64,
) -> UserSession:
    now = datetime.now(UTC)
    record = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(hours=1),
        last_seen_at=now,
    )
    session.add(record)
    session.commit()
    return record


def test_user_session_stores_digest_and_expiry(session: Session) -> None:
    user = add_user(session)

    record = add_session(session, user.id)

    assert record.id is not None
    assert record.user_id == user.id
    assert record.token_hash == "a" * 64
    assert record.revoked_at is None
    assert record.expires_at > record.created_at


def test_user_session_token_digest_must_be_unique(session: Session) -> None:
    user = add_user(session)
    add_session(session, user.id)

    with pytest.raises(IntegrityError):
        add_session(session, user.id)


def test_user_session_rejects_digest_with_wrong_length(session: Session) -> None:
    user = add_user(session)
    now = datetime.now(UTC)
    record = UserSession(
        user_id=user.id,
        token_hash="too-short",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        last_seen_at=now,
    )
    session.add(record)

    with pytest.raises(IntegrityError):
        session.commit()


def test_user_session_can_be_revoked(session: Session) -> None:
    user = add_user(session)
    record = add_session(session, user.id)

    revoked_at = datetime.now(UTC)
    record.revoked_at = revoked_at
    session.commit()
    session.refresh(record)

    assert record.revoked_at is not None
