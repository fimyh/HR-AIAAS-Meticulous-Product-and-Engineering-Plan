"""Create audit and privacy governance tables.

Revision ID: 0008_audit_privacy
Revises: 0007_recruitment_workflows
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008_audit_privacy"
down_revision: str | None = "0007_recruitment_workflows"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_public_id", sa.String(length=100), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_audit_events_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(op.f("ix_audit_events_created_at"), "audit_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_events_resource_type"), "audit_events", ["resource_type"], unique=False)

    op.create_table(
        "retention_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("retention_days > 0", name=op.f("ck_retention_rules_positive_days")),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], name=op.f("fk_retention_rules_updated_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retention_rules")),
        sa.UniqueConstraint("resource_type", name=op.f("uq_retention_rules_resource_type")),
    )

    op.create_table(
        "deletion_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], name=op.f("fk_deletion_requests_approved_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_deletion_requests_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], name=op.f("fk_deletion_requests_requested_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deletion_requests")),
    )

    op.create_table(
        "legal_holds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_legal_holds_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_legal_holds_created_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_legal_holds")),
    )


def downgrade() -> None:
    op.drop_table("legal_holds")
    op.drop_table("deletion_requests")
    op.drop_table("retention_rules")
    op.drop_index(op.f("ix_audit_events_resource_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_created_at"), table_name="audit_events")
    op.drop_table("audit_events")
