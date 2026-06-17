"""Add tenant-owned integration connections.

Revision ID: 20260618_0011
Revises: 20260618_0010
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0011"
down_revision = "20260618_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_integration_connections",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("adapter_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("mapping_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dd_integration_connections_adapter_key",
        "dd_integration_connections",
        ["adapter_key"],
    )
    op.create_index("ix_dd_integration_connections_created_at", "dd_integration_connections", ["created_at"])
    op.create_index("ix_dd_integration_connections_status", "dd_integration_connections", ["status"])
    op.create_index("ix_dd_integration_connections_tenant_id", "dd_integration_connections", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_integration_connections_tenant_id", table_name="dd_integration_connections")
    op.drop_index("ix_dd_integration_connections_status", table_name="dd_integration_connections")
    op.drop_index("ix_dd_integration_connections_created_at", table_name="dd_integration_connections")
    op.drop_index("ix_dd_integration_connections_adapter_key", table_name="dd_integration_connections")
    op.drop_table("dd_integration_connections")
