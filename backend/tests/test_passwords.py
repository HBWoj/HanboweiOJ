import pytest

from app.passwords import (
    MAX_PASSWORD_BYTES,
    hash_password,
    verify_password,
)


def test_hash_password_uses_argon2id_and_does_not_store_plaintext() -> None:
    password = "A secure test phrase 2026!"
    password_hash = hash_password(password)

    assert password_hash.startswith("$argon2id$")
    assert password not in password_hash


def test_hash_password_generates_a_unique_salt() -> None:
    password = "Same password for two test hashes"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_verify_password_accepts_the_correct_password() -> None:
    password = "Correct test password"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_an_incorrect_password() -> None:
    password_hash = hash_password("Correct test password")

    assert verify_password("Incorrect test password", password_hash) is False


def test_password_hashing_supports_unicode_passwords() -> None:
    password = "学习信息学！密码测试🔐"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


@pytest.mark.parametrize(
    "password",
    [
        "",
        "a" * (MAX_PASSWORD_BYTES + 1),
        "中" * (MAX_PASSWORD_BYTES // 3 + 1),
    ],
)
def test_hash_password_rejects_empty_or_oversized_passwords(
    password: str,
) -> None:
    with pytest.raises(ValueError):
        hash_password(password)


def test_hash_password_rejects_non_string_values() -> None:
    with pytest.raises(TypeError):
        hash_password(None)  # type: ignore[arg-type]


def test_verify_password_fails_closed_for_malformed_hashes() -> None:
    assert verify_password("Any non-empty password", "not-a-valid-hash") is False


def test_verify_password_rejects_non_string_hash_values() -> None:
    with pytest.raises(TypeError):
        verify_password("Any non-empty password", None)  # type: ignore[arg-type]
