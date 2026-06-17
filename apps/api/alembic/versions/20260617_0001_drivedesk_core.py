"""Create DriveDesk core foundation tables.

Revision ID: 20260617_0001
Revises:
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260617_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dd_tenants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_tenants_slug", "dd_tenants", ["slug"], unique=True)
    op.create_index("ix_dd_tenants_status", "dd_tenants", ["status"])

    op.create_table(
        "dd_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=True),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dd_audit_events_actor_id", "dd_audit_events", ["actor_id"])
    op.create_index("ix_dd_audit_events_created_at", "dd_audit_events", ["created_at"])
    op.create_index("ix_dd_audit_events_entity_id", "dd_audit_events", ["entity_id"])
    op.create_index("ix_dd_audit_events_entity_type", "dd_audit_events", ["entity_type"])
    op.create_index("ix_dd_audit_events_event_type", "dd_audit_events", ["event_type"])
    op.create_index("ix_dd_audit_events_tenant_id", "dd_audit_events", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_dd_audit_events_tenant_id", table_name="dd_audit_events")
    op.drop_index("ix_dd_audit_events_event_type", table_name="dd_audit_events")
    op.drop_index("ix_dd_audit_events_entity_type", table_name="dd_audit_events")
    op.drop_index("ix_dd_audit_events_entity_id", table_name="dd_audit_events")
    op.drop_index("ix_dd_audit_events_created_at", table_name="dd_audit_events")
    op.drop_index("ix_dd_audit_events_actor_id", table_name="dd_audit_events")
    op.drop_table("dd_audit_events")
    op.drop_index("ix_dd_tenants_status", table_name="dd_tenants")
    op.drop_index("ix_dd_tenants_slug", table_name="dd_tenants")
    op.drop_table("dd_tenants")
