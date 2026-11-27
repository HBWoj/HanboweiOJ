import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import authenticate_user
from app.db import Base
from app.models import User
from app.passwords import hash_password


@pytest.fixture
def session():
    """Provide an isolated in-memory database for each authentication test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


def add_user(
    session: Session,
    *,
    username: str = "student001",
    password: str = "A valid test password!",
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        display_name="Test Student",
        password_hash=hash_password(password),
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    return user


def test_authenticate_user_accepts_valid_credentials(session: Session) -> None:
    expected_user = add_user(session)

    authenticated = authenticate_user(
        session,
        "student001",
        "A valid test password!",
    )

    assert authenticated is not None
    assert authenticated.id == expected_user.id


def test_authenticate_user_normalizes_username_case(session: Session) -> None:
    expected_user = add_user(session, username="student002")

    authenticated = authenticate_user(
        session,
        "STUDENT002",
        "A valid test password!",
    )

    assert authenticated is not None
    assert authenticated.id == expected_user.id


def test_authenticate_user_rejects_incorrect_password(session: Session) -> None:
    add_user(session)

    assert authenticate_user(session, "student001", "Wrong password!") is None


def test_authenticate_user_rejects_unknown_username(session: Session) -> None:
    assert (
        authenticate_user(
            session,
            "unknown001",
            "A valid test password!",
        )
        is None
    )


def test_authenticate_user_rejects_inactive_account(session: Session) -> None:
    add_user(session, is_active=False)

    assert (
        authenticate_user(
            session,
            "student001",
            "A valid test password!",
        )
        is None
    )


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("invalid username", "A valid test password!"),
        ("student001", ""),
        ("student001", "x" * 1025),
    ],
)
def test_authenticate_user_rejects_invalid_input(
    session: Session,
    username: str,
    password: str,
) -> None:
    assert authenticate_user(session, username, password) is None


def test_authenticate_user_rejects_non_string_inputs(session: Session) -> None:
    assert authenticate_user(session, None, "A valid test password!") is None  # type: ignore[arg-type]
    assert authenticate_user(session, "student001", None) is None  # type: ignore[arg-type]
