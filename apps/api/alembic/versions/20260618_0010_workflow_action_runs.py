"""Add workflow action run history.

Revision ID: 20260618_0010
Revises: 20260618_0009
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0010"
down_revision = "20260618_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_workflow_action_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("workflow_rule_id", sa.String(length=36), nullable=False),
        sa.Column("trigger_event_type", sa.String(length=128), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_record_id", sa.String(length=36), nullable=False),
        sa.Column("source_record_type", sa.String(length=32), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=True),
        sa.Column("outbox_event_id", sa.String(length=36), nullable=True),
        sa.Column("task_record_id", sa.String(length=36), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_workflow_action_runs_action_type", "dd_workflow_action_runs", ["action_type"])
    op.create_index("ix_dd_workflow_action_runs_created_at", "dd_workflow_action_runs", ["created_at"])
    op.create_index("ix_dd_workflow_action_runs_new_status", "dd_workflow_action_runs", ["new_status"])
    op.create_index("ix_dd_workflow_action_runs_outbox_event_id", "dd_workflow_action_runs", ["outbox_event_id"])
    op.create_index("ix_dd_workflow_action_runs_previous_status", "dd_workflow_action_runs", ["previous_status"])
    op.create_index("ix_dd_workflow_action_runs_source_record_id", "dd_workflow_action_runs", ["source_record_id"])
    op.create_index("ix_dd_workflow_action_runs_source_record_type", "dd_workflow_action_runs", ["source_record_type"])
    op.create_index("ix_dd_workflow_action_runs_status", "dd_workflow_action_runs", ["status"])
    op.create_index("ix_dd_workflow_action_runs_task_record_id", "dd_workflow_action_runs", ["task_record_id"])
    op.create_index("ix_dd_workflow_action_runs_tenant_id", "dd_workflow_action_runs", ["tenant_id"])
    op.create_index("ix_dd_workflow_action_runs_trigger_event_type", "dd_workflow_action_runs", ["trigger_event_type"])
    op.create_index("ix_dd_workflow_action_runs_workflow_rule_id", "dd_workflow_action_runs", ["workflow_rule_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_workflow_action_runs_workflow_rule_id", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_trigger_event_type", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_tenant_id", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_task_record_id", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_status", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_source_record_type", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_source_record_id", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_previous_status", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_outbox_event_id", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_new_status", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_created_at", table_name="dd_workflow_action_runs")
    op.drop_index("ix_dd_workflow_action_runs_action_type", table_name="dd_workflow_action_runs")
    op.drop_table("dd_workflow_action_runs")
