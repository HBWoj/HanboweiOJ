"""Username normalization and validation utilities."""

import re

USERNAME_PATTERN = re.compile(r"[a-zA-Z0-9_-]{3,32}\Z")


def normalize_username(username: str) -> str:
    """Validate a username and return its lowercase canonical form.

    Whitespace is intentionally rejected instead of silently stripped.
    """
    if not isinstance(username, str):
        raise TypeError("Username must be a string.")

    if USERNAME_PATTERN.fullmatch(username) is None:
        raise ValueError(
            "Username must contain 3 to 32 ASCII letters, digits, underscores, or hyphens."
        )

    return username.lower()
