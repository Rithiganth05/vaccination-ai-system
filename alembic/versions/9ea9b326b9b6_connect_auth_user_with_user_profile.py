"""connect auth user with user profile

Revision ID: 9ea9b326b9b6
Revises:
Create Date: 2026-10-03 19:20:57.569698
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9ea9b326b9b6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add the column temporarily as nullable
    op.add_column(
        "users",
        sa.Column(
            "auth_user_id",
            sa.Integer(),
            nullable=True
        )
    )

    # Step 2: Add foreign key
    op.create_foreign_key(
        "fk_users_auth_user_id",
        "users",
        "auth_users",
        ["auth_user_id"],
        ["auth_user_id"]
    )

    # Step 3: Add unique constraint
    op.create_unique_constraint(
        "uq_users_auth_user_id",
        "users",
        ["auth_user_id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_users_auth_user_id",
        "users",
        type_="unique"
    )

    op.drop_constraint(
        "fk_users_auth_user_id",
        "users",
        type_="foreignkey"
    )

    op.drop_column(
        "users",
        "auth_user_id"
    )