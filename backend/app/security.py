"""CSRF and browser-origin validation primitives for cookie-based sessions.

These helpers are intentionally framework-independent. HTTP routes must call
both CSRF verification and origin validation for state-changing browser requests.
"""

import hashlib
import hmac
import secrets
from collections.abc import Collection
from urllib.parse import urlsplit


def _secret_bytes(secret: str | bytes) -> bytes:
    """Validate and encode the application CSRF signing secret."""
    if isinstance(secret, str):
        value = secret.encode("utf-8")
    elif isinstance(secret, bytes):
        value = secret
    else:
        raise TypeError("CSRF secret must be a string or bytes.")

    if len(value) < 32:
        raise ValueError("CSRF secret must contain at least 32 bytes.")
    return value


def create_csrf_token(secret: str | bytes) -> str:
    """Create a signed double-submit CSRF token using a fresh random nonce."""
    key = _secret_bytes(secret)
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(key, nonce.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{nonce}.{signature}"


def verify_csrf_token(
    cookie_token: str | None,
    request_token: str | None,
    secret: str | bytes,
) -> bool:
    """Verify matching cookie/header tokens and their HMAC signature."""
    if (
        not isinstance(cookie_token, str)
        or not isinstance(request_token, str)
        or not cookie_token
        or len(cookie_token) > 256
        or len(request_token) > 256
    ):
        return False

    key = _secret_bytes(secret)
    if not hmac.compare_digest(cookie_token, request_token):
        return False

    try:
        nonce, supplied_signature = cookie_token.rsplit(".", 1)
        nonce.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        return False

    if not nonce or len(supplied_signature) != 64:
        return False

    expected_signature = hmac.new(
        key,
        nonce.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(supplied_signature, expected_signature)


def _is_valid_origin(value: str) -> bool:
    """Accept only serialized HTTP(S) origins, not paths or opaque URLs."""
    if not isinstance(value, str) or not value or value == "*":
        return False
    try:
        parsed = urlsplit(value)
        _ = parsed.port
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and parsed.path == ""
            and parsed.query == ""
            and parsed.fragment == ""
        )
    except ValueError:
        return False


def validate_request_origin(
    origin: str | None,
    allowed_origins: Collection[str],
) -> bool:
    """Require an exact allowlisted browser Origin for state-changing requests."""
    if not isinstance(origin, str) or not _is_valid_origin(origin):
        return False

    allowed = {
        candidate
        for candidate in allowed_origins
        if isinstance(candidate, str) and _is_valid_origin(candidate)
    }
    return origin in allowed
