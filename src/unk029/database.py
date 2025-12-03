"""
Database configuration and connection management for Oracle.
"""

from collections.abc import Generator
from contextlib import contextmanager
import os

from dotenv import load_dotenv
import oracledb

load_dotenv()


class DatabaseConfig:
    """Database configuration holder."""

    def __init__(
        self, user: str | None = None, password: str | None = None, dsn: str | None = None
    ):
        self.user = user or os.getenv("ORACLE_USER")
        self.password = password or os.getenv("ORACLE_PASSWORD")
        self.dsn = dsn or os.getenv("ORACLE_DSN")

    def validate(self) -> bool:
        """Check if all required config is present."""
        return all([self.user, self.password, self.dsn])


# Default configuration (uses environment variables)
_default_config = DatabaseConfig()


def get_connection(config: DatabaseConfig | None = None) -> oracledb.Connection:
    """Get Oracle database connection."""
    cfg = config or _default_config
    return oracledb.connect(user=cfg.user, password=cfg.password, dsn=cfg.dsn)


@contextmanager
def get_cursor(config: DatabaseConfig | None = None) -> Generator[oracledb.Cursor, None, None]:
    """Context manager for database cursor."""
    conn = get_connection(config)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()
