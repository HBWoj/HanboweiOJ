"""Server-side session lifecycle helpers.

Raw session tokens are returned only at creation time. Persisted records contain
only SHA-256 token digests, so database reads cannot be used as browser tokens.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import User, UserSession


def _utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    """Interpret naive database datetimes as UTC and normalize aware values."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _token_digest(token: str) -> str | None:
    """Return a token digest, rejecting empty or non-string input."""
    if not isinstance(token, str) or not token:
        return None
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(
    db: Session,
    user_id,
    lifetime: timedelta,
) -> tuple[str, UserSession]:
    """Create a session and return its one-time raw token plus database record.

    The caller must deliver the raw token only through a protected transport
    such as an HttpOnly cookie. This function never commits the transaction.
    """
    if not isinstance(lifetime, timedelta) or lifetime <= timedelta(0):
        raise ValueError("Session lifetime must be a positive timedelta.")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise ValueError("An active user is required to create a session.")

    now = _utc_now()
    raw_token = secrets.token_urlsafe(32)
    record = UserSession(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
        created_at=now,
        expires_at=now + lifetime,
        last_seen_at=now,
    )
    db.add(record)
    db.flush()
    return raw_token, record


def resolve_session(
    db: Session,
    raw_token: str,
    *,
    now: datetime | None = None,
) -> User | None:
    """Return the active account for a valid, unexpired, non-revoked token."""
    digest = _token_digest(raw_token)
    if digest is None:
        return None

    current_time = now or _utc_now()
    if current_time.tzinfo is None:
        raise ValueError("The validation time must be timezone-aware.")
    current_time = current_time.astimezone(UTC)

    record = db.scalar(
        select(UserSession).where(UserSession.token_hash == digest)
    )
    if record is None or record.revoked_at is not None:
        return None
    if _as_utc(record.expires_at) <= current_time:
        return None

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        return None

    return user


def revoke_session(
    db: Session,
    raw_token: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Revoke one session; return False for unknown or already revoked tokens."""
    digest = _token_digest(raw_token)
    if digest is None:
        return False

    record = db.scalar(
        select(UserSession).where(UserSession.token_hash == digest)
    )
    if record is None or record.revoked_at is not None:
        return False

    revoked_at = now or _utc_now()
    if revoked_at.tzinfo is None:
        raise ValueError("The revocation time must be timezone-aware.")
    record.revoked_at = revoked_at.astimezone(UTC)
    db.flush()
    return True


def revoke_all_sessions(
    db: Session,
    user_id,
    *,
    now: datetime | None = None,
) -> int:
    """Revoke every non-revoked session for a user and return the row count."""
    revoked_at = now or _utc_now()
    if revoked_at.tzinfo is None:
        raise ValueError("The revocation time must be timezone-aware.")

    result = db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at.astimezone(UTC))
    )
    return result.rowcount or 0
