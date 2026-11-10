"""Create candidate profile tables.

Revision ID: 0003_candidate_core
Revises: 0002_identity_and_access
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_candidate_core"
down_revision: str | None = "0002_identity_and_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("current_title", sa.String(length=200), nullable=True),
        sa.Column("professional_summary", sa.Text(), nullable=True),
        sa.Column("profile_status", sa.String(length=50), nullable=False),
        sa.Column("source_language", sa.String(length=20), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_candidates_created_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidates")),
        sa.UniqueConstraint("public_id", name=op.f("uq_candidates_public_id")),
    )
    op.create_index(op.f("ix_candidates_profile_status"), "candidates", ["profile_status"], unique=False)

    op.create_table(
        "candidate_contacts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("contact_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_candidate_contacts_candidate_id_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_contacts")),
    )
    op.create_index(op.f("ix_candidate_contacts_candidate_id"), "candidate_contacts", ["candidate_id"], unique=False)

    op.create_table(
        "experiences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("job_title", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_experiences_candidate_id_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiences")),
    )

    op.create_table(
        "education_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("institution_name", sa.String(length=250), nullable=False),
        sa.Column("degree_name", sa.String(length=250), nullable=True),
        sa.Column("field_of_study", sa.String(length=250), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_education_records_candidate_id_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_education_records")),
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("normalized_name", sa.String(length=150), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
        sa.UniqueConstraint("normalized_name", name=op.f("uq_skills_normalized_name")),
    )

    op.create_table(
        "candidate_skills",
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("proficiency_level", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name=op.f("ck_candidate_skills_confidence_range")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_candidate_skills_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name=op.f("fk_candidate_skills_skill_id_skills"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("candidate_id", "skill_id", name=op.f("pk_candidate_skills")),
    )

    op.create_table(
        "certifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=False),
        sa.Column("issuer", sa.String(length=250), nullable=True),
        sa.Column("issued_at", sa.Date(), nullable=True),
        sa.Column("expires_at", sa.Date(), nullable=True),
        sa.Column("credential_id", sa.String(length=200), nullable=True),
        sa.Column("credential_url", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_certifications_candidate_id_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_certifications")),
    )

    op.create_table(
        "candidate_languages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("language_code", sa.String(length=20), nullable=True),
        sa.Column("language_name", sa.String(length=100), nullable=False),
        sa.Column("proficiency_level", sa.String(length=50), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name=op.f("ck_candidate_languages_confidence_range")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_candidate_languages_candidate_id_candidates"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_languages")),
    )


def downgrade() -> None:
    op.drop_table("candidate_languages")
    op.drop_table("certifications")
    op.drop_table("candidate_skills")
    op.drop_table("skills")
    op.drop_table("education_records")
    op.drop_table("experiences")
    op.drop_index(op.f("ix_candidate_contacts_candidate_id"), table_name="candidate_contacts")
    op.drop_table("candidate_contacts")
    op.drop_index(op.f("ix_candidates_profile_status"), table_name="candidates")
    op.drop_table("candidates")
