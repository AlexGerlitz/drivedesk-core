"""Add integration connection checks.

Revision ID: 20260618_0013
Revises: 20260618_0012
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0013"
down_revision = "20260618_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_integration_connection_checks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("integration_connection_id", sa.String(length=36), nullable=False),
        sa.Column("adapter_key", sa.String(length=128), nullable=False),
        sa.Column("check_type", sa.String(length=64), nullable=False, server_default="synthetic_preflight"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dd_integration_connection_checks_tenant_id",
        "dd_integration_connection_checks",
        ["tenant_id"],
    )
    op.create_index(
        "ix_dd_integration_connection_checks_integration_connection_id",
        "dd_integration_connection_checks",
        ["integration_connection_id"],
    )
    op.create_index(
        "ix_dd_integration_connection_checks_adapter_key",
        "dd_integration_connection_checks",
        ["adapter_key"],
    )
    op.create_index(
        "ix_dd_integration_connection_checks_check_type",
        "dd_integration_connection_checks",
        ["check_type"],
    )
    op.create_index(
        "ix_dd_integration_connection_checks_status",
        "dd_integration_connection_checks",
        ["status"],
    )
    op.create_index(
        "ix_dd_integration_connection_checks_created_at",
        "dd_integration_connection_checks",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dd_integration_connection_checks_created_at", table_name="dd_integration_connection_checks")
    op.drop_index("ix_dd_integration_connection_checks_status", table_name="dd_integration_connection_checks")
    op.drop_index("ix_dd_integration_connection_checks_check_type", table_name="dd_integration_connection_checks")
    op.drop_index("ix_dd_integration_connection_checks_adapter_key", table_name="dd_integration_connection_checks")
    op.drop_index(
        "ix_dd_integration_connection_checks_integration_connection_id",
        table_name="dd_integration_connection_checks",
    )
    op.drop_index("ix_dd_integration_connection_checks_tenant_id", table_name="dd_integration_connection_checks")
    op.drop_table("dd_integration_connection_checks")
