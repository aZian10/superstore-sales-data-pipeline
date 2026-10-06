"""Database connection and execution utilities."""

from contextlib import contextmanager
from typing import Generator
import sqlalchemy as sa
from sqlalchemy.engine import Engine, Connection

from src.utils.config import db_config
from src.utils.logger import get_logger

logger = get_logger("db")

_engine: Engine | None = None


def get_engine() -> Engine:
    """Returns a singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = sa.create_engine(
            db_config.connection_uri,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


@contextmanager
def get_connection() -> Generator[Connection, None, None]:
    """Yields a managed database connection within a transaction block."""
    engine = get_engine()
    with engine.begin() as conn:
        yield conn


def execute_sql_file(file_path: str, connection: Connection | None = None) -> None:
    """Reads and executes a SQL script file."""
    logger.info(f"Executing SQL file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split statements by semicolon where appropriate, or execute directly
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    if connection is not None:
        for stmt in statements:
            connection.execute(sa.text(stmt))
    else:
        with get_connection() as conn:
            for stmt in statements:
                conn.execute(sa.text(stmt))
