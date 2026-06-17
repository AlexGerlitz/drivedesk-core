"""Add dedicated platform admin grants.

Revision ID: 20260618_0007
Revises: 20260618_0006
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0007"
down_revision = "20260618_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_platform_admins",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role", name="uq_dd_platform_admins_user_role"),
    )
    op.create_index("ix_dd_platform_admins_role", "dd_platform_admins", ["role"])
    op.create_index("ix_dd_platform_admins_status", "dd_platform_admins", ["status"])
    op.create_index("ix_dd_platform_admins_user_id", "dd_platform_admins", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_platform_admins_user_id", table_name="dd_platform_admins")
    op.drop_index("ix_dd_platform_admins_status", table_name="dd_platform_admins")
    op.drop_index("ix_dd_platform_admins_role", table_name="dd_platform_admins")
    op.drop_table("dd_platform_admins")
