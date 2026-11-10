"""Create AI governance and extraction tables.

Revision ID: 0005_ai_extraction
Revises: 0004_documents_ingestion
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_ai_extraction"
down_revision: str | None = "0004_documents_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=True),
        sa.Column("digest", sa.String(length=255), nullable=True),
        sa.Column("context_size", sa.Integer(), nullable=True),
        sa.Column("embedding_dimension", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_registry")),
        sa.UniqueConstraint("name", "version", "digest", name="uq_model_registry_identity"),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt_key", sa.String(length=150), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("output_schema", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], name=op.f("fk_prompt_versions_approved_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_prompt_versions_created_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_versions")),
        sa.UniqueConstraint("prompt_key", "version_number", name="uq_prompt_versions_key_version"),
    )

    op.create_table(
        "extraction_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_version_id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("prompt_version_id", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)", name=op.f("ck_extraction_runs_confidence_range")),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], name=op.f("fk_extraction_runs_document_version_id_document_versions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["model_registry.id"], name=op.f("fk_extraction_runs_model_id_model_registry")),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], name=op.f("fk_extraction_runs_prompt_version_id_prompt_versions")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extraction_runs")),
    )

    op.create_table(
        "extracted_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("extraction_run_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("field_path", sa.String(length=300), nullable=False),
        sa.Column("value_type", sa.String(length=50), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("review_status", sa.String(length=50), nullable=False),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name=op.f("ck_extracted_facts_confidence_range")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_extracted_facts_candidate_id_candidates"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["extraction_run_id"], ["extraction_runs.id"], name=op.f("fk_extracted_facts_extraction_run_id_extraction_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], name=op.f("fk_extracted_facts_reviewed_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extracted_facts")),
    )

    op.create_table(
        "fact_evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("extracted_fact_id", sa.Integer(), nullable=False),
        sa.Column("text_block_id", sa.Integer(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["extracted_fact_id"], ["extracted_facts.id"], name=op.f("fk_fact_evidence_extracted_fact_id_extracted_facts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["text_block_id"], ["document_text_blocks.id"], name=op.f("fk_fact_evidence_text_block_id_document_text_blocks"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fact_evidence")),
    )

    op.create_table(
        "ai_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("prompt_version_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("run_type", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("resource_public_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("safe_error_code", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["model_registry.id"], name=op.f("fk_ai_runs_model_id_model_registry")),
        sa.ForeignKeyConstraint(["prompt_version_id"], ["prompt_versions.id"], name=op.f("fk_ai_runs_prompt_version_id_prompt_versions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_ai_runs_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_runs")),
    )


def downgrade() -> None:
    op.drop_table("ai_runs")
    op.drop_table("fact_evidence")
    op.drop_table("extracted_facts")
    op.drop_table("extraction_runs")
    op.drop_table("prompt_versions")
    op.drop_table("model_registry")
