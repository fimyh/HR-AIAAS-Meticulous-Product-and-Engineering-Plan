"""Create database foundation.

Revision ID: 0001_database_foundation
Revises:
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_database_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_metadata",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_system_metadata")),
    )


def downgrade() -> None:
    op.drop_table("system_metadata")
