"""Normalize usernames and enforce canonical username constraints.

Revision ID: 0002_normalize_usernames
Revises: 0001_users
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_normalize_usernames"
down_revision = "0001_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Validate existing data, then normalize and constrain usernames."""
    connection = op.get_bind()

    invalid_length = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM users
            WHERE length(username) < 3 OR length(username) > 32
            """
        )
    ).scalar_one()

    invalid_characters = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM users
            WHERE username !~ '^[A-Za-z0-9_-]+$'
            """
        )
    ).scalar_one()

    lowercase_collisions = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT lower(username)
                FROM users
                GROUP BY lower(username)
                HAVING COUNT(*) > 1
            ) AS collisions
            """
        )
    ).scalar_one()

    if invalid_length or invalid_characters or lowercase_collisions:
        raise RuntimeError(
            "Username migration aborted: "
            f"invalid_length={invalid_length}, "
            f"invalid_characters={invalid_characters}, "
            f"lowercase_collisions={lowercase_collisions}. "
            "Resolve the affected records before retrying."
        )

    # Existing mixed-case usernames are safe to normalize after preflight.
    connection.execute(
        sa.text(
            """
            UPDATE users
            SET username = lower(username)
            WHERE username <> lower(username)
            """
        )
    )

    # The unique constraint already guarantees uniqueness.
    # This separate non-unique index is redundant.
    op.drop_index("ix_users_username", table_name="users")

    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=64),
        type_=sa.String(length=32),
        existing_nullable=False,
    )

    op.create_check_constraint(
        "ck_users_username_length",
        "users",
        "length(username) BETWEEN 3 AND 32",
    )

    op.create_check_constraint(
        "ck_users_username_lowercase",
        "users",
        "username = lower(username)",
    )


def downgrade() -> None:
    """Remove the new constraints.

    Note: usernames normalized during upgrade remain lowercase after downgrade.
    """
    op.drop_constraint(
        "ck_users_username_lowercase",
        "users",
        type_="check",
    )

    op.drop_constraint(
        "ck_users_username_length",
        "users",
        type_="check",
    )

    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=False,
    )

    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        unique=False,
    )
