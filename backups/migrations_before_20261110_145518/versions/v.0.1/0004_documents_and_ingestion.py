"""Create document and ingestion tables.

Revision ID: 0004_documents_ingestion
Revises: 0003_candidate_core
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_documents_ingestion"
down_revision: str | None = "0003_candidate_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_documents_candidate_id_candidates"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], name=op.f("fk_documents_uploaded_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("public_id", name=op.f("uq_documents_public_id")),
        sa.UniqueConstraint("sha256", name=op.f("uq_documents_sha256")),
    )

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=1000), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_versions_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_versions")),
        sa.UniqueConstraint("document_id", "version_number", name="uq_document_versions_document_version"),
        sa.UniqueConstraint("storage_key", name=op.f("uq_document_versions_storage_key")),
    )

    op.create_table(
        "document_text_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_version_id", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_name", sa.String(length=200), nullable=True),
        sa.Column("block_index", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], name=op.f("fk_document_text_blocks_document_version_id_document_versions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_text_blocks")),
        sa.UniqueConstraint("document_version_id", "block_index", name="uq_document_text_blocks_version_block"),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("document_version_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("maximum_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("current_stage", sa.String(length=50), nullable=True),
        sa.Column("safe_error_code", sa.String(length=100), nullable=True),
        sa.Column("safe_error_message", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], name=op.f("fk_ingestion_jobs_document_version_id_document_versions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_jobs")),
        sa.UniqueConstraint("public_id", name=op.f("uq_ingestion_jobs_public_id")),
    )
    op.create_index(op.f("ix_ingestion_jobs_status"), "ingestion_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_jobs_status"), table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_table("document_text_blocks")
    op.drop_table("document_versions")
    op.drop_table("documents")
