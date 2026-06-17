"""Add auth lifecycle attempt audit table.

Revision ID: 20260618_0006
Revises: 20260618_0005
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0006"
down_revision = "20260618_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_auth_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_auth_attempts_created_at", "dd_auth_attempts", ["created_at"])
    op.create_index("ix_dd_auth_attempts_email", "dd_auth_attempts", ["email"])
    op.create_index("ix_dd_auth_attempts_outcome", "dd_auth_attempts", ["outcome"])
    op.create_index("ix_dd_auth_attempts_reason", "dd_auth_attempts", ["reason"])
    op.create_index("ix_dd_auth_attempts_user_id", "dd_auth_attempts", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_auth_attempts_user_id", table_name="dd_auth_attempts")
    op.drop_index("ix_dd_auth_attempts_reason", table_name="dd_auth_attempts")
    op.drop_index("ix_dd_auth_attempts_outcome", table_name="dd_auth_attempts")
    op.drop_index("ix_dd_auth_attempts_email", table_name="dd_auth_attempts")
    op.drop_index("ix_dd_auth_attempts_created_at", table_name="dd_auth_attempts")
    op.drop_table("dd_auth_attempts")
