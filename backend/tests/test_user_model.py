import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import User, UserRole


def test_user_model_persists_safe_account_fields() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    user_id = uuid.uuid4()

    with Session(engine) as session:
        user = User(
            id=user_id,
            username="student001",
            display_name="Student One",
            password_hash="argon2id-test-hash",
            role=UserRole.STUDENT.value,
        )
        session.add(user)
        session.commit()

        saved = session.scalar(select(User).where(User.id == user_id))
        assert saved is not None
        assert saved.username == "student001"
        assert saved.role == "student"
        assert saved.is_active is True
        assert saved.password_hash == "argon2id-test-hash"
