"""Create 0002 identity and access tables.

Revision ID: 0002_identity_and_access
Revises: 0001_database_foundation
"""
from alembic import op

revision = '0002_identity_and_access'
down_revision = '74c2eeb48ea8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, public_id VARCHAR(36) NOT NULL UNIQUE, email VARCHAR(320) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, full_name VARCHAR(200) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, is_superuser BOOLEAN NOT NULL DEFAULT 0, last_login_at DATETIME, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE roles (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE, description TEXT, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE permissions (id INTEGER PRIMARY KEY, code VARCHAR(150) NOT NULL UNIQUE, resource VARCHAR(100) NOT NULL, action VARCHAR(100) NOT NULL, description TEXT, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE user_roles (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE, assigned_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL, assigned_at DATETIME NOT NULL, PRIMARY KEY(user_id, role_id))')
    op.execute('CREATE TABLE role_permissions (role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE, permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE, assigned_at DATETIME NOT NULL, PRIMARY KEY(role_id, permission_id))')
    op.execute('CREATE TABLE sessions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, token_hash VARCHAR(255) NOT NULL UNIQUE, expires_at DATETIME NOT NULL, last_activity_at DATETIME NOT NULL, revoked_at DATETIME, created_at DATETIME NOT NULL)')
    op.execute('CREATE TABLE login_events (id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, email_attempted VARCHAR(320) NOT NULL, result VARCHAR(50) NOT NULL, ip_address VARCHAR(64), user_agent VARCHAR(500), created_at DATETIME NOT NULL)')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS login_events")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS role_permissions")
    op.execute("DROP TABLE IF EXISTS user_roles")
    op.execute("DROP TABLE IF EXISTS permissions")
    op.execute("DROP TABLE IF EXISTS roles")
    op.execute("DROP TABLE IF EXISTS users")



