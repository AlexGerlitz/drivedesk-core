"""Add integration reconciliations.

Revision ID: 20260618_0014
Revises: 20260618_0013
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0014"
down_revision = "20260618_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_integration_reconciliations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("outbox_event_id", sa.String(length=36), nullable=False),
        sa.Column("adapter_key", sa.String(length=128), nullable=False),
        sa.Column("operation_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("expected_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("actual_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("diff_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_integration_reconciliations_tenant_id", "dd_integration_reconciliations", ["tenant_id"])
    op.create_index(
        "ix_dd_integration_reconciliations_outbox_event_id",
        "dd_integration_reconciliations",
        ["outbox_event_id"],
    )
    op.create_index("ix_dd_integration_reconciliations_adapter_key", "dd_integration_reconciliations", ["adapter_key"])
    op.create_index("ix_dd_integration_reconciliations_operation_key", "dd_integration_reconciliations", ["operation_key"])
    op.create_index("ix_dd_integration_reconciliations_status", "dd_integration_reconciliations", ["status"])
    op.create_index("ix_dd_integration_reconciliations_created_at", "dd_integration_reconciliations", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_dd_integration_reconciliations_created_at", table_name="dd_integration_reconciliations")
    op.drop_index("ix_dd_integration_reconciliations_status", table_name="dd_integration_reconciliations")
    op.drop_index("ix_dd_integration_reconciliations_operation_key", table_name="dd_integration_reconciliations")
    op.drop_index("ix_dd_integration_reconciliations_adapter_key", table_name="dd_integration_reconciliations")
    op.drop_index("ix_dd_integration_reconciliations_outbox_event_id", table_name="dd_integration_reconciliations")
    op.drop_index("ix_dd_integration_reconciliations_tenant_id", table_name="dd_integration_reconciliations")
    op.drop_table("dd_integration_reconciliations")
