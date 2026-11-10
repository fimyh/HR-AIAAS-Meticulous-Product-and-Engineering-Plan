"""Create 0005 ai extraction tables.

Revision ID: 0005_ai_extraction
Revises: 0004_documents_and_ingestion
"""
from alembic import op

revision = '0005_ai_extraction'
down_revision = '0004_documents_and_ingestion'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE model_registry (id INTEGER PRIMARY KEY, name VARCHAR(200) NOT NULL, model_type VARCHAR(50) NOT NULL, provider VARCHAR(100) NOT NULL, version VARCHAR(100), digest VARCHAR(255), context_size INTEGER, embedding_dimension INTEGER, is_active BOOLEAN NOT NULL DEFAULT 1, created_at DATETIME NOT NULL, UNIQUE(name, version, digest))')
    op.execute('CREATE TABLE prompt_versions (id INTEGER PRIMARY KEY, prompt_key VARCHAR(150) NOT NULL, version_number INTEGER NOT NULL, purpose TEXT NOT NULL, template TEXT NOT NULL, output_schema TEXT, status VARCHAR(50) NOT NULL, created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, approved_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at DATETIME NOT NULL, approved_at DATETIME, UNIQUE(prompt_key, version_number))')
    op.execute('CREATE TABLE extraction_runs (id INTEGER PRIMARY KEY, document_version_id INTEGER NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE, model_id INTEGER NOT NULL REFERENCES model_registry(id), prompt_version_id INTEGER NOT NULL REFERENCES prompt_versions(id), schema_version VARCHAR(100) NOT NULL, status VARCHAR(50) NOT NULL, overall_confidence FLOAT CHECK(overall_confidence IS NULL OR (overall_confidence >= 0 AND overall_confidence <= 1)), started_at DATETIME NOT NULL, completed_at DATETIME)')
    op.execute('CREATE TABLE extracted_facts (id INTEGER PRIMARY KEY, extraction_run_id INTEGER NOT NULL REFERENCES extraction_runs(id) ON DELETE CASCADE, candidate_id INTEGER REFERENCES candidates(id) ON DELETE SET NULL, field_path VARCHAR(300) NOT NULL, value_type VARCHAR(50) NOT NULL, value_json TEXT NOT NULL, confidence FLOAT CHECK(confidence IS NULL OR (confidence >= 0 AND confidence <= 1)), review_status VARCHAR(50) NOT NULL, reviewed_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reviewed_at DATETIME, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE fact_evidence (id INTEGER PRIMARY KEY, extracted_fact_id INTEGER NOT NULL REFERENCES extracted_facts(id) ON DELETE CASCADE, text_block_id INTEGER NOT NULL REFERENCES document_text_blocks(id) ON DELETE CASCADE, start_offset INTEGER, end_offset INTEGER, evidence_text TEXT, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE ai_runs (id INTEGER PRIMARY KEY, model_id INTEGER NOT NULL REFERENCES model_registry(id), prompt_version_id INTEGER REFERENCES prompt_versions(id) ON DELETE SET NULL, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, run_type VARCHAR(100) NOT NULL, resource_type VARCHAR(100), resource_public_id VARCHAR(100), status VARCHAR(50) NOT NULL, input_tokens INTEGER, output_tokens INTEGER, duration_ms INTEGER, safe_error_code VARCHAR(100), created_at DATETIME NOT NULL, completed_at DATETIME)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_runs")
    op.execute("DROP TABLE IF EXISTS fact_evidence")
    op.execute("DROP TABLE IF EXISTS extracted_facts")
    op.execute("DROP TABLE IF EXISTS extraction_runs")
    op.execute("DROP TABLE IF EXISTS prompt_versions")
    op.execute("DROP TABLE IF EXISTS model_registry")
