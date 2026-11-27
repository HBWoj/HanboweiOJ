import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import Base
from app.models import User


def create_test_engine():
    """创建独立的 SQLite 内存测试数据库。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


def test_user_model_persists_safe_account_fields() -> None:
    """测试用户基本信息能够正确保存。"""
    engine = create_test_engine()
    user_id = uuid.uuid4()

    with Session(engine) as session:
        user = User(
            id=user_id,
            username="student001",
            display_name="Student One",
            password_hash="argon2id-test-hash",
            role="student",
        )
        session.add(user)
        session.commit()

        saved = session.scalar(select(User).where(User.id == user_id))

        assert saved is not None
        assert saved.username == "student001"
        assert saved.display_name == "Student One"
        assert saved.role == "student"
        assert saved.is_active is True
        assert saved.password_hash == "argon2id-test-hash"

    engine.dispose()


def test_user_model_generates_default_values() -> None:
    """测试 UUID、默认角色、默认状态和时间字段。"""
    engine = create_test_engine()

    with Session(engine) as session:
        user = User(
            username="student002",
            display_name="Student Two",
            password_hash="argon2id-test-hash",
        )
        session.add(user)
        session.commit()

        saved = session.scalar(select(User).where(User.username == "student002"))

        assert saved is not None
        assert isinstance(saved.id, uuid.UUID)
        assert saved.role == "student"
        assert saved.is_active is True
        assert saved.created_at is not None
        assert saved.updated_at is not None

    engine.dispose()


def test_duplicate_username_is_rejected() -> None:
    """测试重复用户名不能写入数据库。"""
    engine = create_test_engine()

    with Session(engine) as session:
        first_user = User(
            username="student003",
            display_name="Student Three",
            password_hash="test-hash-1",
        )
        second_user = User(
            username="student003",
            display_name="Another Student",
            password_hash="test-hash-2",
        )

        session.add(first_user)
        session.commit()

        session.add(second_user)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    engine.dispose()


def test_invalid_user_role_is_rejected() -> None:
    """测试数据库拒绝不在允许范围内的角色。"""
    engine = create_test_engine()

    with Session(engine) as session:
        user = User(
            username="student004",
            display_name="Invalid Role User",
            password_hash="test-hash",
            role="superuser",
        )
        session.add(user)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    engine.dispose()


def test_user_active_status_can_be_updated() -> None:
    """测试用户停用状态能够正确保存。"""
    engine = create_test_engine()

    with Session(engine) as session:
        user = User(
            username="student005",
            display_name="Student Five",
            password_hash="test-hash",
        )
        session.add(user)
        session.commit()

        user.is_active = False
        session.commit()

        saved = session.scalar(select(User).where(User.username == "student005"))

        assert saved is not None
        assert saved.is_active is False

    engine.dispose()


def test_user_model_normalizes_username() -> None:
    """用户名在 ORM 写入前统一转换为小写。"""
    engine = create_test_engine()

    with Session(engine) as session:
        user = User(
            username="Student006",
            display_name="Student Six",
            password_hash="test-hash",
        )
        session.add(user)
        session.commit()

        saved = session.scalar(select(User).where(User.username == "student006"))

        assert saved is not None
        assert saved.username == "student006"

    engine.dispose()


def test_username_with_different_case_is_duplicate() -> None:
    """大小写不同的同一用户名不能创建两个账户。"""
    engine = create_test_engine()

    with Session(engine) as session:
        first_user = User(
            username="Student007",
            display_name="Student Seven",
            password_hash="test-hash-1",
        )
        second_user = User(
            username="STUDENT007",
            display_name="Another Student",
            password_hash="test-hash-2",
        )

        session.add(first_user)
        session.commit()

        session.add(second_user)

        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()

    engine.dispose()


def test_username_with_invalid_characters_is_rejected() -> None:
    """用户名包含非法字符时不能通过 ORM 验证。"""

    with pytest.raises(ValueError):
        User(
            username="student@008",
            display_name="Invalid Username",
            password_hash="test-hash",
        )
