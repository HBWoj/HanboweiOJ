"""Credential authentication service without HTTP or session concerns."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.passwords import hash_password, verify_password
from app.username import normalize_username

# A process-local dummy hash makes unknown-account attempts perform an Argon2id
# verification too. It is not an account credential and is never persisted.
_DUMMY_PASSWORD_HASH = hash_password("hanboweioj-non-account-dummy-value")


def authenticate_user(
    session: Session,
    username: str,
    password: str,
) -> User | None:
    """Return an active user for valid credentials; otherwise return None.

    The function deliberately uses the same failure result for unknown users,
    inactive users, and incorrect passwords. It does not create sessions,
    issue tokens, mutate account state, or expose account-existence details.
    """
    try:
        canonical_username = normalize_username(username)
    except (TypeError, ValueError):
        canonical_username = None

    user = None
    if canonical_username is not None:
        user = session.scalar(
            select(User).where(User.username == canonical_username)
        )

    # Verify against a real or dummy hash so unknown usernames do not skip the
    # expensive password-verification step.
    stored_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    try:
        password_matches = verify_password(password, stored_hash)
    except (TypeError, ValueError):
        return None

    if user is None or not user.is_active or not password_matches:
        return None

    return user
