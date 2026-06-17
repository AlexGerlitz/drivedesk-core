"""Add integration adapter outbox fields.

Revision ID: 20260617_0003
Revises: 20260617_0002
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260617_0003"
down_revision = "20260617_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dd_outbox_events", sa.Column("adapter_key", sa.String(length=128), nullable=True))
    op.add_column("dd_outbox_events", sa.Column("result_json", sa.Text(), nullable=True))
    op.add_column("dd_outbox_events", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("dd_outbox_events", sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_dd_outbox_events_adapter_key", "dd_outbox_events", ["adapter_key"])
    op.create_index("ix_dd_outbox_events_next_retry_at", "dd_outbox_events", ["next_retry_at"])


def downgrade() -> None:
    op.drop_index("ix_dd_outbox_events_next_retry_at", table_name="dd_outbox_events")
    op.drop_index("ix_dd_outbox_events_adapter_key", table_name="dd_outbox_events")
    op.drop_column("dd_outbox_events", "dead_lettered_at")
    op.drop_column("dd_outbox_events", "next_retry_at")
    op.drop_column("dd_outbox_events", "result_json")
    op.drop_column("dd_outbox_events", "adapter_key")
