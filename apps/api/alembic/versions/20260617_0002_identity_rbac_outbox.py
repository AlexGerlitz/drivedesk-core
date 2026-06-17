"""Add identity, membership RBAC, and outbox foundation.

Revision ID: 20260617_0002
Revises: 20260617_0001
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260617_0002"
down_revision = "20260617_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_users_email", "dd_users", ["email"], unique=True)
    op.create_index("ix_dd_users_status", "dd_users", ["status"])

    op.create_table(
        "dd_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_dd_memberships_tenant_user"),
    )
    op.create_index("ix_dd_memberships_role", "dd_memberships", ["role"])
    op.create_index("ix_dd_memberships_status", "dd_memberships", ["status"])
    op.create_index("ix_dd_memberships_tenant_id", "dd_memberships", ["tenant_id"])
    op.create_index("ix_dd_memberships_user_id", "dd_memberships", ["user_id"])

    op.create_table(
        "dd_outbox_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_outbox_events_created_at", "dd_outbox_events", ["created_at"])
    op.create_index("ix_dd_outbox_events_event_type", "dd_outbox_events", ["event_type"])
    op.create_index("ix_dd_outbox_events_status", "dd_outbox_events", ["status"])
    op.create_index("ix_dd_outbox_events_tenant_id", "dd_outbox_events", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_outbox_events_tenant_id", table_name="dd_outbox_events")
    op.drop_index("ix_dd_outbox_events_status", table_name="dd_outbox_events")
    op.drop_index("ix_dd_outbox_events_event_type", table_name="dd_outbox_events")
    op.drop_index("ix_dd_outbox_events_created_at", table_name="dd_outbox_events")
    op.drop_table("dd_outbox_events")
    op.drop_index("ix_dd_memberships_user_id", table_name="dd_memberships")
    op.drop_index("ix_dd_memberships_tenant_id", table_name="dd_memberships")
    op.drop_index("ix_dd_memberships_status", table_name="dd_memberships")
    op.drop_index("ix_dd_memberships_role", table_name="dd_memberships")
    op.drop_table("dd_memberships")
    op.drop_index("ix_dd_users_status", table_name="dd_users")
    op.drop_index("ix_dd_users_email", table_name="dd_users")
    op.drop_table("dd_users")
