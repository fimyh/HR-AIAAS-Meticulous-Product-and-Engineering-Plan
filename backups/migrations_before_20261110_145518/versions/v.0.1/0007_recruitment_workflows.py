"""Create shortlists and talent pool tables.

Revision ID: 0007_recruitment_workflows
Revises: 0006_jobs_matching
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007_recruitment_workflows"
down_revision: str | None = "0006_jobs_matching"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "shortlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_shortlists_created_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_shortlists_job_id_jobs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shortlists")),
        sa.UniqueConstraint("job_id", "name", name="uq_shortlists_job_name"),
    )

    op.create_table(
        "shortlist_entries",
        sa.Column("shortlist_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["added_by_id"], ["users.id"], name=op.f("fk_shortlist_entries_added_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_shortlist_entries_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shortlist_id"], ["shortlists.id"], name=op.f("fk_shortlist_entries_shortlist_id_shortlists"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("shortlist_id", "candidate_id", name=op.f("pk_shortlist_entries")),
    )

    op.create_table(
        "talent_pools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_talent_pools_created_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_talent_pools")),
        sa.UniqueConstraint("name", name=op.f("uq_talent_pools_name")),
    )

    op.create_table(
        "talent_pool_memberships",
        sa.Column("talent_pool_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["added_by_id"], ["users.id"], name=op.f("fk_talent_pool_memberships_added_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_talent_pool_memberships_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["talent_pool_id"], ["talent_pools.id"], name=op.f("fk_talent_pool_memberships_talent_pool_id_talent_pools"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("talent_pool_id", "candidate_id", name=op.f("pk_talent_pool_memberships")),
    )


def downgrade() -> None:
    op.drop_table("talent_pool_memberships")
    op.drop_table("talent_pools")
    op.drop_table("shortlist_entries")
    op.drop_table("shortlists")
