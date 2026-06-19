"""Add business control tower tables.

Revision ID: 20260619_0016
Revises: 20260618_0015
Create Date: 2026-06-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260619_0016"
down_revision = "20260618_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_business_state_observations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("system_key", sa.String(length=128), nullable=False),
        sa.Column("subject_type", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_business_state_observations_tenant_id", "dd_business_state_observations", ["tenant_id"])
    op.create_index("ix_dd_business_state_observations_system_key", "dd_business_state_observations", ["system_key"])
    op.create_index("ix_dd_business_state_observations_subject_type", "dd_business_state_observations", ["subject_type"])
    op.create_index("ix_dd_business_state_observations_subject_id", "dd_business_state_observations", ["subject_id"])
    op.create_index("ix_dd_business_state_observations_external_ref", "dd_business_state_observations", ["external_ref"])
    op.create_index("ix_dd_business_state_observations_state", "dd_business_state_observations", ["state"])
    op.create_index("ix_dd_business_state_observations_observed_at", "dd_business_state_observations", ["observed_at"])
    op.create_index("ix_dd_business_state_observations_created_at", "dd_business_state_observations", ["created_at"])

    op.create_table(
        "dd_business_exceptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("exception_type", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("subject_type", sa.String(length=64), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("impact_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("evidence_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_business_exceptions_tenant_id", "dd_business_exceptions", ["tenant_id"])
    op.create_index("ix_dd_business_exceptions_exception_type", "dd_business_exceptions", ["exception_type"])
    op.create_index("ix_dd_business_exceptions_severity", "dd_business_exceptions", ["severity"])
    op.create_index("ix_dd_business_exceptions_status", "dd_business_exceptions", ["status"])
    op.create_index("ix_dd_business_exceptions_subject_type", "dd_business_exceptions", ["subject_type"])
    op.create_index("ix_dd_business_exceptions_subject_id", "dd_business_exceptions", ["subject_id"])
    op.create_index("ix_dd_business_exceptions_detected_at", "dd_business_exceptions", ["detected_at"])
    op.create_index("ix_dd_business_exceptions_created_at", "dd_business_exceptions", ["created_at"])

    op.create_table(
        "dd_repair_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("business_exception_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=128), nullable=False),
        sa.Column("safety_level", sa.String(length=32), nullable=False),
        sa.Column("requires_approval", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="proposed"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_repair_actions_tenant_id", "dd_repair_actions", ["tenant_id"])
    op.create_index("ix_dd_repair_actions_business_exception_id", "dd_repair_actions", ["business_exception_id"])
    op.create_index("ix_dd_repair_actions_action_type", "dd_repair_actions", ["action_type"])
    op.create_index("ix_dd_repair_actions_safety_level", "dd_repair_actions", ["safety_level"])
    op.create_index("ix_dd_repair_actions_requires_approval", "dd_repair_actions", ["requires_approval"])
    op.create_index("ix_dd_repair_actions_status", "dd_repair_actions", ["status"])
    op.create_index("ix_dd_repair_actions_created_at", "dd_repair_actions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_dd_repair_actions_created_at", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_status", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_requires_approval", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_safety_level", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_action_type", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_business_exception_id", table_name="dd_repair_actions")
    op.drop_index("ix_dd_repair_actions_tenant_id", table_name="dd_repair_actions")
    op.drop_table("dd_repair_actions")

    op.drop_index("ix_dd_business_exceptions_created_at", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_detected_at", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_subject_id", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_subject_type", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_status", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_severity", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_exception_type", table_name="dd_business_exceptions")
    op.drop_index("ix_dd_business_exceptions_tenant_id", table_name="dd_business_exceptions")
    op.drop_table("dd_business_exceptions")

    op.drop_index("ix_dd_business_state_observations_created_at", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_observed_at", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_state", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_external_ref", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_subject_id", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_subject_type", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_system_key", table_name="dd_business_state_observations")
    op.drop_index("ix_dd_business_state_observations_tenant_id", table_name="dd_business_state_observations")
    op.drop_table("dd_business_state_observations")
