"""Create 0003 candidate core tables.

Revision ID: 0003_candidate_core
Revises: 0002_identity_and_access
"""
from alembic import op

revision = '0003_candidate_core'
down_revision = '0002_identity_and_access'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE candidates (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, full_name VARCHAR(200) NOT NULL, current_title VARCHAR(200), professional_summary TEXT, profile_status VARCHAR(50) NOT NULL, source_language VARCHAR(20), is_archived BOOLEAN NOT NULL DEFAULT 0, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, archived_at DATETIME)')
    op.execute('CREATE TABLE candidate_contacts (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, contact_type VARCHAR(50) NOT NULL, value VARCHAR(500) NOT NULL, is_primary BOOLEAN NOT NULL DEFAULT 0, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE experiences (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, company_name VARCHAR(200) NOT NULL, job_title VARCHAR(200) NOT NULL, start_date DATE, end_date DATE, is_current BOOLEAN NOT NULL DEFAULT 0, description TEXT, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE education_records (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, institution_name VARCHAR(250) NOT NULL, degree_name VARCHAR(250), field_of_study VARCHAR(250), start_date DATE, end_date DATE, description TEXT, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE skills (id INTEGER PRIMARY KEY, normalized_name VARCHAR(150) NOT NULL UNIQUE, display_name VARCHAR(150) NOT NULL, category VARCHAR(100), is_active BOOLEAN NOT NULL DEFAULT 1, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE candidate_skills (candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE, proficiency_level VARCHAR(50), confidence FLOAT CHECK(confidence IS NULL OR (confidence >= 0 AND confidence <= 1)), evidence_summary TEXT, last_used_at DATETIME, created_at DATETIME NOT NULL, PRIMARY KEY(candidate_id, skill_id))')
    op.execute('CREATE TABLE certifications (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, name VARCHAR(250) NOT NULL, issuer VARCHAR(250), issued_at DATE, expires_at DATE, credential_id VARCHAR(200), credential_url VARCHAR(1000), created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE candidate_languages (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, language_code VARCHAR(20), language_name VARCHAR(100) NOT NULL, proficiency_level VARCHAR(50), confidence FLOAT CHECK(confidence IS NULL OR (confidence >= 0 AND confidence <= 1)), created_at DATETIME NOT NULL)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS candidate_languages")
    op.execute("DROP TABLE IF EXISTS certifications")
    op.execute("DROP TABLE IF EXISTS candidate_skills")
    op.execute("DROP TABLE IF EXISTS skills")
    op.execute("DROP TABLE IF EXISTS education_records")
    op.execute("DROP TABLE IF EXISTS experiences")
    op.execute("DROP TABLE IF EXISTS candidate_contacts")
    op.execute("DROP TABLE IF EXISTS candidates")
