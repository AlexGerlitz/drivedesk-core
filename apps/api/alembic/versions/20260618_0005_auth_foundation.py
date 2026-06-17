"""Add credential auth and access token foundation.

Revision ID: 20260618_0005
Revises: 20260617_0004
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0005"
down_revision = "20260617_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dd_users", sa.Column("credential_hash", sa.Text(), nullable=True))

    op.create_table(
        "dd_access_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_access_tokens_expires_at", "dd_access_tokens", ["expires_at"])
    op.create_index("ix_dd_access_tokens_status", "dd_access_tokens", ["status"])
    op.create_index("ix_dd_access_tokens_token_hash", "dd_access_tokens", ["token_hash"], unique=True)
    op.create_index("ix_dd_access_tokens_user_id", "dd_access_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_access_tokens_user_id", table_name="dd_access_tokens")
    op.drop_index("ix_dd_access_tokens_token_hash", table_name="dd_access_tokens")
    op.drop_index("ix_dd_access_tokens_status", table_name="dd_access_tokens")
    op.drop_index("ix_dd_access_tokens_expires_at", table_name="dd_access_tokens")
    op.drop_table("dd_access_tokens")
    op.drop_column("dd_users", "credential_hash")
