"""Create 0008 audit and privacy tables.

Revision ID: 0008_audit_and_privacy
Revises: 0007_recruitment_workflows
"""
from alembic import op

revision = '0008_audit_and_privacy'
down_revision = '0007_recruitment_workflows'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE audit_events (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, action VARCHAR(150) NOT NULL, resource_type VARCHAR(100) NOT NULL, resource_public_id VARCHAR(100), outcome VARCHAR(50) NOT NULL, reason TEXT, details_json TEXT, request_id VARCHAR(100), ip_address VARCHAR(64), created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE retention_rules (id INTEGER PRIMARY KEY, resource_type VARCHAR(100) NOT NULL UNIQUE, retention_days INTEGER NOT NULL CHECK(retention_days > 0), is_active BOOLEAN NOT NULL DEFAULT 1, updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE deletion_requests (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, status VARCHAR(50) NOT NULL, reason TEXT NOT NULL, requested_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, approved_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, requested_at DATETIME NOT NULL, approved_at DATETIME, completed_at DATETIME)')
    op.execute('CREATE TABLE legal_holds (id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE, reason TEXT NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, released_at DATETIME)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS legal_holds")
    op.execute("DROP TABLE IF EXISTS deletion_requests")
    op.execute("DROP TABLE IF EXISTS retention_rules")
    op.execute("DROP TABLE IF EXISTS audit_events")
