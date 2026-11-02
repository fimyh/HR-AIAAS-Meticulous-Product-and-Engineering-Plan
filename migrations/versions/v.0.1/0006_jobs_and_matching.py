"""Create jobs, scorecards, and deterministic matching tables.

Revision ID: 0006_jobs_matching
Revises: 0005_ai_extraction
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0006_jobs_matching"
down_revision: str | None = "0005_ai_extraction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("department", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=250), nullable=True),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_jobs_created_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("public_id", name=op.f("uq_jobs_public_id")),
    )

    op.create_table(
        "job_requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=True),
        sa.Column("requirement_type", sa.String(length=50), nullable=False),
        sa.Column("required_level", sa.String(length=50), nullable=True),
        sa.Column("minimum_years", sa.Integer(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_job_requirements_job_id_jobs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], name=op.f("fk_job_requirements_skill_id_skills"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_requirements")),
    )

    op.create_table(
        "scorecards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], name=op.f("fk_scorecards_approved_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_scorecards_created_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_scorecards_job_id_jobs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scorecards")),
        sa.UniqueConstraint("job_id", "version_number", name="uq_scorecards_job_version"),
    )

    op.create_table(
        "scorecard_criteria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scorecard_id", sa.Integer(), nullable=False),
        sa.Column("criterion_code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("configuration_json", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.CheckConstraint("weight >= 0 AND weight <= 100", name=op.f("ck_scorecard_criteria_weight_range")),
        sa.ForeignKeyConstraint(["scorecard_id"], ["scorecards.id"], name=op.f("fk_scorecard_criteria_scorecard_id_scorecards"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scorecard_criteria")),
        sa.UniqueConstraint("scorecard_id", "criterion_code", name="uq_scorecard_criteria_code"),
    )

    op.create_table(
        "match_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("scorecard_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name=op.f("fk_match_runs_created_by_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], name=op.f("fk_match_runs_job_id_jobs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scorecard_id"], ["scorecards.id"], name=op.f("fk_match_runs_scorecard_id_scorecards")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_runs")),
        sa.UniqueConstraint("public_id", name=op.f("uq_match_runs_public_id")),
    )

    op.create_table(
        "candidate_job_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("match_run_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("match_label", sa.String(length=100), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("total_score >= 0 AND total_score <= 100", name=op.f("ck_candidate_job_scores_total_score_range")),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name=op.f("fk_candidate_job_scores_candidate_id_candidates"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["match_run_id"], ["match_runs.id"], name=op.f("fk_candidate_job_scores_match_run_id_match_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_job_scores")),
        sa.UniqueConstraint("match_run_id", "candidate_id", name="uq_candidate_job_scores_run_candidate"),
    )

    op.create_table(
        "score_contributions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_job_score_id", sa.Integer(), nullable=False),
        sa.Column("criterion_id", sa.Integer(), nullable=False),
        sa.Column("awarded_points", sa.Float(), nullable=False),
        sa.Column("maximum_points", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.Text(), nullable=True),
        sa.CheckConstraint("awarded_points >= 0", name=op.f("ck_score_contributions_awarded_nonnegative")),
        sa.CheckConstraint("maximum_points >= 0", name=op.f("ck_score_contributions_maximum_nonnegative")),
        sa.ForeignKeyConstraint(["candidate_job_score_id"], ["candidate_job_scores.id"], name=op.f("fk_score_contributions_candidate_job_score_id_candidate_job_scores"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["criterion_id"], ["scorecard_criteria.id"], name=op.f("fk_score_contributions_criterion_id_scorecard_criteria")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_contributions")),
    )


def downgrade() -> None:
    op.drop_table("score_contributions")
    op.drop_table("candidate_job_scores")
    op.drop_table("match_runs")
    op.drop_table("scorecard_criteria")
    op.drop_table("scorecards")
    op.drop_table("job_requirements")
    op.drop_table("jobs")
