from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from hr_aiaas.db.base import Base

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    department: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(250))
    employment_type: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class JobRequirement(Base):
    __tablename__ = "job_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[int | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    requirement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    required_level: Mapped[str | None] = mapped_column(String(50))
    minimum_years: Mapped[int | None] = mapped_column(Integer)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class Scorecard(Base):
    __tablename__ = "scorecards"
    __table_args__ = (UniqueConstraint("job_id", "version_number", name="uq_scorecards_job_version"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class ScorecardCriterion(Base):
    __tablename__ = "scorecard_criteria"
    __table_args__ = (UniqueConstraint("scorecard_id", "criterion_code", name="uq_scorecard_criteria_code"), CheckConstraint("weight >= 0 AND weight <= 100", name="ck_scorecard_criteria_weight_range"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scorecard_id: Mapped[int] = mapped_column(ForeignKey("scorecards.id", ondelete="CASCADE"), nullable=False)
    criterion_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    configuration_json: Mapped[str | None] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

class MatchRun(Base):
    __tablename__ = "match_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    scorecard_id: Mapped[int] = mapped_column(ForeignKey("scorecards.id"), nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class CandidateJobScore(Base):
    __tablename__ = "candidate_job_scores"
    __table_args__ = (UniqueConstraint("match_run_id", "candidate_id", name="uq_candidate_job_scores_run_candidate"), CheckConstraint("total_score >= 0 AND total_score <= 100", name="ck_candidate_job_scores_total_score_range"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_run_id: Mapped[int] = mapped_column(ForeignKey("match_runs.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_label: Mapped[str] = mapped_column(String(100), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class ScoreContribution(Base):
    __tablename__ = "score_contributions"
    __table_args__ = (CheckConstraint("awarded_points >= 0", name="ck_score_contributions_awarded_nonnegative"), CheckConstraint("maximum_points >= 0", name="ck_score_contributions_maximum_nonnegative"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_job_score_id: Mapped[int] = mapped_column(ForeignKey("candidate_job_scores.id", ondelete="CASCADE"), nullable=False)
    criterion_id: Mapped[int] = mapped_column(ForeignKey("scorecard_criteria.id"), nullable=False)
    awarded_points: Mapped[float] = mapped_column(Float, nullable=False)
    maximum_points: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    evidence_json: Mapped[str | None] = mapped_column(Text)
