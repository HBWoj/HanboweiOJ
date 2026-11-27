from datetime import UTC, datetime, timedelta
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import User, UserSession
from app.sessions import (
    create_session,
    resolve_session,
    revoke_all_sessions,
    revoke_session,
)


@pytest.fixture
def session():
    """Create an isolated database for session lifecycle tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def add_user(session: Session, *, is_active: bool = True) -> User:
    user = User(
        username="student001",
        display_name="Test Student",
        password_hash="test-hash-not-used-for-authentication",
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    return user


def test_create_session_returns_raw_token_but_stores_only_digest(
    session: Session,
) -> None:
    user = add_user(session)

    raw_token, record = create_session(session, user.id, timedelta(hours=1))

    assert len(raw_token) >= 40
    assert record.user_id == user.id
    assert record.token_hash != raw_token
    assert len(record.token_hash) == 64
    assert record.expires_at > record.created_at


def test_create_session_requires_active_user(session: Session) -> None:
    user = add_user(session, is_active=False)

    with pytest.raises(ValueError, match="active user"):
        create_session(session, user.id, timedelta(hours=1))

    with pytest.raises(ValueError, match="active user"):
        create_session(session, uuid.uuid4(), timedelta(hours=1))


@pytest.mark.parametrize("lifetime", [timedelta(0), timedelta(seconds=-1), None])
def test_create_session_rejects_invalid_lifetime(
    session: Session,
    lifetime: timedelta | None,
) -> None:
    user = add_user(session)

    with pytest.raises(ValueError, match="positive timedelta"):
        create_session(session, user.id, lifetime)  # type: ignore[arg-type]


def test_resolve_session_accepts_valid_token(session: Session) -> None:
    user = add_user(session)
    raw_token, _ = create_session(session, user.id, timedelta(hours=1))

    resolved_user = resolve_session(session, raw_token)

    assert resolved_user is not None
    assert resolved_user.id == user.id


def test_resolve_session_rejects_unknown_empty_and_non_string_tokens(
    session: Session,
) -> None:
    assert resolve_session(session, "not-a-session-token") is None
    assert resolve_session(session, "") is None
    assert resolve_session(session, None) is None  # type: ignore[arg-type]


def test_resolve_session_rejects_expired_token(session: Session) -> None:
    user = add_user(session)
    raw_token, record = create_session(session, user.id, timedelta(seconds=1))

    resolved_user = resolve_session(
        session,
        raw_token,
        now=record.expires_at + timedelta(seconds=1),
    )

    assert resolved_user is None


def test_resolve_session_rejects_revoked_token(session: Session) -> None:
    user = add_user(session)
    raw_token, _ = create_session(session, user.id, timedelta(hours=1))
    assert revoke_session(session, raw_token) is True

    assert resolve_session(session, raw_token) is None


def test_resolve_session_rejects_disabled_account(session: Session) -> None:
    user = add_user(session)
    raw_token, _ = create_session(session, user.id, timedelta(hours=1))
    user.is_active = False
    session.flush()

    assert resolve_session(session, raw_token) is None


def test_revoke_session_is_idempotent(session: Session) -> None:
    user = add_user(session)
    raw_token, _ = create_session(session, user.id, timedelta(hours=1))

    assert revoke_session(session, raw_token) is True
    assert revoke_session(session, raw_token) is False
    assert revoke_session(session, "unknown-token") is False


def test_revoke_all_sessions_revokes_only_target_users_sessions(
    session: Session,
) -> None:
    first_user = add_user(session)
    first_token, _ = create_session(session, first_user.id, timedelta(hours=1))
    second_user = User(
        username="student002",
        display_name="Second Student",
        password_hash="test-hash-not-used-for-authentication",
    )
    session.add(second_user)
    session.commit()
    second_token, _ = create_session(session, second_user.id, timedelta(hours=1))

    assert revoke_all_sessions(session, first_user.id) == 1
    assert resolve_session(session, first_token) is None
    assert resolve_session(session, second_token) is not None
    assert revoke_all_sessions(session, first_user.id) == 0
