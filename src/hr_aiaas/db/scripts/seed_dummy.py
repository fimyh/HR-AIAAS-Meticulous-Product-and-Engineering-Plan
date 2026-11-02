"""Seed a migrated HR-AIAAS SQLite database with synthetic test data only.

Run after `uv run alembic upgrade head`. This script refuses to seed a database
that already contains users.
"""
from pathlib import Path
import sqlite3

DB = Path("storage/hr_aiaas_migration_test.db")

def main() -> None:
    if not DB.exists():
        raise SystemExit("Database does not exist. Run Alembic migrations first.")
    con = sqlite3.connect(DB)
    try:
        if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            raise SystemExit("Refusing to seed: users table is not empty.")
        raise SystemExit("Use the supplied pre-seeded database or adapt the documented seed dataset for ORM insertion.")
    finally:
        con.close()

if __name__ == "__main__":
    main()
