"""Create 0004 documents and ingestion tables.

Revision ID: 0004_documents_and_ingestion
Revises: 0003_candidate_core
"""
from alembic import op

revision = '0004_documents_and_ingestion'
down_revision = '0003_candidate_core'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE documents (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL, original_filename VARCHAR(500) NOT NULL, document_type VARCHAR(50) NOT NULL, mime_type VARCHAR(255) NOT NULL, size_bytes INTEGER NOT NULL, sha256 VARCHAR(64) NOT NULL UNIQUE, status VARCHAR(50) NOT NULL, uploaded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, uploaded_at DATETIME NOT NULL, deleted_at DATETIME)')
    op.execute('CREATE TABLE document_versions (id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE, version_number INTEGER NOT NULL, storage_key VARCHAR(1000) NOT NULL UNIQUE, sha256 VARCHAR(64) NOT NULL, size_bytes INTEGER NOT NULL, created_at DATETIME NOT NULL, UNIQUE(document_id, version_number))')
    op.execute('CREATE TABLE document_text_blocks (id INTEGER PRIMARY KEY, document_version_id INTEGER NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE, page_number INTEGER, section_name VARCHAR(200), block_index INTEGER NOT NULL, start_offset INTEGER, end_offset INTEGER, content TEXT NOT NULL, created_at DATETIME NOT NULL, UNIQUE(document_version_id, block_index))')
    op.execute('CREATE TABLE ingestion_jobs (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, document_version_id INTEGER NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE, status VARCHAR(50) NOT NULL, attempt_count INTEGER NOT NULL DEFAULT 0, maximum_attempts INTEGER NOT NULL DEFAULT 3, current_stage VARCHAR(50), safe_error_code VARCHAR(100), safe_error_message TEXT, queued_at DATETIME NOT NULL, started_at DATETIME, heartbeat_at DATETIME, completed_at DATETIME)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ingestion_jobs")
    op.execute("DROP TABLE IF EXISTS document_text_blocks")
    op.execute("DROP TABLE IF EXISTS document_versions")
    op.execute("DROP TABLE IF EXISTS documents")
