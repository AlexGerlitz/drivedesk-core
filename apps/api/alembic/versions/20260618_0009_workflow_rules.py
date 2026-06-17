"""Add tenant-owned workflow rule foundation.

Revision ID: 20260618_0009
Revises: 20260618_0008
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0009"
down_revision = "20260618_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_workflow_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trigger_event_type", sa.String(length=128), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=True),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("action_config_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_workflow_rules_action_type", "dd_workflow_rules", ["action_type"])
    op.create_index("ix_dd_workflow_rules_created_at", "dd_workflow_rules", ["created_at"])
    op.create_index("ix_dd_workflow_rules_from_status", "dd_workflow_rules", ["from_status"])
    op.create_index("ix_dd_workflow_rules_record_type", "dd_workflow_rules", ["record_type"])
    op.create_index("ix_dd_workflow_rules_status", "dd_workflow_rules", ["status"])
    op.create_index("ix_dd_workflow_rules_tenant_id", "dd_workflow_rules", ["tenant_id"])
    op.create_index("ix_dd_workflow_rules_to_status", "dd_workflow_rules", ["to_status"])
    op.create_index("ix_dd_workflow_rules_trigger_event_type", "dd_workflow_rules", ["trigger_event_type"])


def downgrade() -> None:
    op.drop_index("ix_dd_workflow_rules_trigger_event_type", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_to_status", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_tenant_id", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_status", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_record_type", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_from_status", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_created_at", table_name="dd_workflow_rules")
    op.drop_index("ix_dd_workflow_rules_action_type", table_name="dd_workflow_rules")
    op.drop_table("dd_workflow_rules")
