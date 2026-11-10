"""Create 0007 recruitment workflows tables.

Revision ID: 0007_recruitment_workflows
Revises: 0006_jobs_and_matching
"""
from alembic import op

revision = '0007_recruitment_workflows'
down_revision = '0006_jobs_and_matching'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE shortlists (id INTEGER PRIMARY KEY, job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, name VARCHAR(200) NOT NULL, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, UNIQUE(job_id, name))')
    op.execute('CREATE TABLE shortlist_entries (shortlist_id INTEGER NOT NULL REFERENCES shortlists(id) ON DELETE CASCADE, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, added_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reason TEXT, added_at DATETIME NOT NULL, PRIMARY KEY(shortlist_id, candidate_id))')
    op.execute('CREATE TABLE talent_pools (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL UNIQUE, description TEXT, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE talent_pool_memberships (talent_pool_id INTEGER NOT NULL REFERENCES talent_pools(id) ON DELETE CASCADE, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, added_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reason TEXT, added_at DATETIME NOT NULL, review_at DATETIME, expires_at DATETIME, PRIMARY KEY(talent_pool_id, candidate_id))')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS talent_pool_memberships")
    op.execute("DROP TABLE IF EXISTS talent_pools")
    op.execute("DROP TABLE IF EXISTS shortlist_entries")
    op.execute("DROP TABLE IF EXISTS shortlists")
