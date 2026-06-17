"""Add integration connection scopes.

Revision ID: 20260618_0012
Revises: 20260618_0011
Create Date: 2026-06-18
"""

from alembic import op
import sqlalchemy as sa

revision = "20260618_0012"
down_revision = "20260618_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "dd_integration_connections",
        sa.Column("scopes_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("dd_integration_connections", "scopes_json")
