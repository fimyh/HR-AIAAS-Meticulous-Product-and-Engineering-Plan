from dataclasses import dataclass

from sqlalchemy import text

from hr_aiaas.db.session import engine


@dataclass(frozen=True, slots=True)
class DatabaseHealth:
    """Result of the database readiness inspection."""

    status: str
    foreign_keys: bool
    journal_mode: str
    busy_timeout_ms: int


async def check_database_health() -> DatabaseHealth:
    """Verify connectivity and required SQLite settings."""
    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT 1"),
        )

        foreign_keys_result = await connection.execute(
            text("PRAGMA foreign_keys"),
        )
        journal_mode_result = await connection.execute(
            text("PRAGMA journal_mode"),
        )
        busy_timeout_result = await connection.execute(
            text("PRAGMA busy_timeout"),
        )

        foreign_keys = int(
            foreign_keys_result.scalar_one(),
        )
        journal_mode = str(
            journal_mode_result.scalar_one(),
        )
        busy_timeout = int(
            busy_timeout_result.scalar_one(),
        )

    return DatabaseHealth(
        status="ready",
        foreign_keys=foreign_keys == 1,
        journal_mode=journal_mode.lower(),
        busy_timeout_ms=busy_timeout,
    )
