"""Add integration incidents.

Revision ID: 20260618_0015
Revises: 20260618_0014
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0015"
down_revision = "20260618_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_integration_incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("adapter_key", sa.String(length=128), nullable=False),
        sa.Column("operation_key", sa.String(length=128), nullable=True),
        sa.Column("runbook_key", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_integration_incidents_tenant_id", "dd_integration_incidents", ["tenant_id"])
    op.create_index("ix_dd_integration_incidents_source_type", "dd_integration_incidents", ["source_type"])
    op.create_index("ix_dd_integration_incidents_source_id", "dd_integration_incidents", ["source_id"])
    op.create_index("ix_dd_integration_incidents_adapter_key", "dd_integration_incidents", ["adapter_key"])
    op.create_index("ix_dd_integration_incidents_operation_key", "dd_integration_incidents", ["operation_key"])
    op.create_index("ix_dd_integration_incidents_runbook_key", "dd_integration_incidents", ["runbook_key"])
    op.create_index("ix_dd_integration_incidents_severity", "dd_integration_incidents", ["severity"])
    op.create_index("ix_dd_integration_incidents_status", "dd_integration_incidents", ["status"])
    op.create_index("ix_dd_integration_incidents_created_at", "dd_integration_incidents", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_dd_integration_incidents_created_at", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_status", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_severity", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_runbook_key", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_operation_key", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_adapter_key", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_source_id", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_source_type", table_name="dd_integration_incidents")
    op.drop_index("ix_dd_integration_incidents_tenant_id", table_name="dd_integration_incidents")
    op.drop_table("dd_integration_incidents")
