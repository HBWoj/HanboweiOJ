"""Password hashing and verification helpers.

Passwords are stored only as Argon2id hashes. Plaintext passwords must never be
written to logs, database fields, or application responses.
"""

from pwdlib import PasswordHash
from pwdlib.exceptions import HashVerificationError, UnknownHashError

# Bound the input size before handing it to the memory-hard hashing algorithm.
MAX_PASSWORD_BYTES = 1024

_password_hasher = PasswordHash.recommended()


def _validate_password(password: str) -> None:
    """Reject invalid password inputs without trimming or normalizing them."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    if not password:
        raise ValueError("Password must not be empty.")

    # Every Unicode code point requires at least one UTF-8 byte. This first
    # check avoids allocating an encoded copy for obviously oversized input.
    if len(password) > MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds the maximum supported length.")

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds the maximum supported length.")


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash for a non-empty password."""
    _validate_password(password)
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches a stored hash.

    Unknown or malformed stored hashes fail closed and return False.
    Invalid password input types or lengths raise a validation exception.
    """
    _validate_password(password)

    if not isinstance(password_hash, str):
        raise TypeError("Password hash must be a string.")

    try:
        return _password_hasher.verify(password, password_hash)
    except (HashVerificationError, UnknownHashError):
        return False
