import pytest

from app.username import normalize_username


@pytest.mark.parametrize(
    ("username", "expected"),
    [
        ("student001", "student001"),
        ("Student001", "student001"),
        ("STUDENT001", "student001"),
        ("abc_123", "abc_123"),
        ("abc-123", "abc-123"),
        ("A1_b-2", "a1_b-2"),
        ("abc", "abc"),
        ("a" * 32, "a" * 32),
    ],
)
def test_normalize_username_accepts_valid_names(
    username: str,
    expected: str,
) -> None:
    assert normalize_username(username) == expected


@pytest.mark.parametrize(
    "username",
    [
        "",
        "ab",
        "a" * 33,
        "student 001",
        "student@001",
        "学生001",
        "student.001",
        " student001",
        "student001 ",
    ],
)
def test_normalize_username_rejects_invalid_names(
    username: str,
) -> None:
    with pytest.raises(ValueError):
        normalize_username(username)


def test_normalize_username_rejects_non_string_values() -> None:
    with pytest.raises(TypeError):
        normalize_username(None)  # type: ignore[arg-type]
