"""Add integration observability fields.

Revision ID: 20260617_0004
Revises: 20260617_0003
Create Date: 2026-06-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260617_0004"
down_revision = "20260617_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dd_outbox_events", sa.Column("last_duration_ms", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("dd_outbox_events", "last_duration_ms")
