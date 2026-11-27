import pytest

from app.security import (
    create_csrf_token,
    validate_request_origin,
    verify_csrf_token,
)

SECRET = "test-only-csrf-secret-with-at-least-32-bytes"


def test_csrf_token_round_trip() -> None:
    token = create_csrf_token(SECRET)

    assert verify_csrf_token(token, token, SECRET) is True


def test_csrf_tokens_use_fresh_nonces() -> None:
    first = create_csrf_token(SECRET)
    second = create_csrf_token(SECRET)

    assert first != second


@pytest.mark.parametrize(
    ("cookie_token", "request_token"),
    [
        (None, None),
        ("", ""),
        ("valid.token", "different.token"),
        ("not-a-signed-token", "not-a-signed-token"),
        ("x" * 257, "x" * 257),
    ],
)
def test_csrf_token_rejects_invalid_values(
    cookie_token: str | None,
    request_token: str | None,
) -> None:
    assert verify_csrf_token(cookie_token, request_token, SECRET) is False


def test_csrf_token_rejects_wrong_secret() -> None:
    token = create_csrf_token(SECRET)

    assert verify_csrf_token(
        token,
        token,
        "a-different-secret-with-at-least-32-bytes",
    ) is False


@pytest.mark.parametrize(
    "secret",
    ["short", b"short", "", b""],
)
def test_csrf_token_rejects_weak_secret(secret: str | bytes) -> None:
    with pytest.raises(ValueError, match="at least 32 bytes"):
        create_csrf_token(secret)


def test_csrf_token_rejects_non_string_secret() -> None:
    with pytest.raises(TypeError, match="string or bytes"):
        create_csrf_token(None)  # type: ignore[arg-type]


def test_origin_accepts_exact_allowlisted_origin() -> None:
    assert validate_request_origin(
        "https://oj.example.test",
        {"https://oj.example.test", "http://localhost:3000"},
    )


@pytest.mark.parametrize(
    "origin",
    [
        None,
        "",
        "null",
        "*",
        "https://oj.example.test.attacker.test",
        "https://oj.example.test/path",
        "https://user@oj.example.test",
        "javascript://oj.example.test",
        "https://oj.example.test?next=attacker",
    ],
)
def test_origin_rejects_untrusted_or_malformed_values(origin: str | None) -> None:
    assert not validate_request_origin(origin, {"https://oj.example.test"})


def test_origin_ignores_invalid_allowlist_entries() -> None:
    assert not validate_request_origin(
        "https://oj.example.test",
        {"*", "https://oj.example.test/path", "not-an-origin"},
    )
