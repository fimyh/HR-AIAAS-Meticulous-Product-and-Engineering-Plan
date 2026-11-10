"""Create 0006 jobs and matching tables.

Revision ID: 0006_jobs_and_matching
Revises: 0005_ai_extraction
"""
from alembic import op

revision = '0006_jobs_and_matching'
down_revision = '0005_ai_extraction'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE jobs (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, title VARCHAR(250) NOT NULL, department VARCHAR(200), location VARCHAR(250), employment_type VARCHAR(100), description TEXT, status VARCHAR(50) NOT NULL, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE job_requirements (id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, skill_id INTEGER REFERENCES skills(id) ON DELETE SET NULL, requirement_type VARCHAR(50) NOT NULL, required_level VARCHAR(50), minimum_years INTEGER, is_mandatory BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE scorecards (id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, version_number INTEGER NOT NULL, status VARCHAR(50) NOT NULL, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, approved_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, approved_at DATETIME, UNIQUE(job_id, version_number))')
    op.execute('CREATE TABLE scorecard_criteria (id INTEGER PRIMARY KEY, scorecard_id INTEGER NOT NULL REFERENCES scorecards(id) ON DELETE CASCADE, criterion_code VARCHAR(100) NOT NULL, name VARCHAR(200) NOT NULL, description TEXT, weight FLOAT NOT NULL CHECK(weight >= 0 AND weight <= 100), configuration_json TEXT, display_order INTEGER NOT NULL, UNIQUE(scorecard_id, criterion_code))')
    op.execute('CREATE TABLE match_runs (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, scorecard_id INTEGER NOT NULL REFERENCES scorecards(id), created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, status VARCHAR(50) NOT NULL, created_at DATETIME NOT NULL, completed_at DATETIME)')
    op.execute('CREATE TABLE candidate_job_scores (id INTEGER PRIMARY KEY, match_run_id INTEGER NOT NULL REFERENCES match_runs(id) ON DELETE CASCADE, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, total_score FLOAT NOT NULL CHECK(total_score >= 0 AND total_score <= 100), match_label VARCHAR(100) NOT NULL, explanation TEXT, created_at DATETIME NOT NULL, UNIQUE(match_run_id, candidate_id))')
    op.execute('CREATE TABLE score_contributions (id INTEGER PRIMARY KEY, candidate_job_score_id INTEGER NOT NULL REFERENCES candidate_job_scores(id) ON DELETE CASCADE, criterion_id INTEGER NOT NULL REFERENCES scorecard_criteria(id), awarded_points FLOAT NOT NULL CHECK(awarded_points >= 0), maximum_points FLOAT NOT NULL CHECK(maximum_points >= 0), explanation TEXT, evidence_json TEXT)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS score_contributions")
    op.execute("DROP TABLE IF EXISTS candidate_job_scores")
    op.execute("DROP TABLE IF EXISTS match_runs")
    op.execute("DROP TABLE IF EXISTS scorecard_criteria")
    op.execute("DROP TABLE IF EXISTS scorecards")
    op.execute("DROP TABLE IF EXISTS job_requirements")
    op.execute("DROP TABLE IF EXISTS jobs")
