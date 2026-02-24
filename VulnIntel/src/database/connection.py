"""Database connection management for VulnIntel."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.config import DATABASE_PATH
from src.database.schema import create_tables


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Get a database connection with optimized settings.
    
    Args:
        db_path: Path to database file (defaults to config DATABASE_PATH)
        
    Returns:
        SQLite connection object
    """
    if db_path is None:
        db_path = DATABASE_PATH
    
    conn = sqlite3.connect(str(db_path))
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Optimize for performance
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = -64000")  # 64 MB cache
    conn.execute("PRAGMA temp_store = MEMORY")
    
    # Return rows as dictionaries
    conn.row_factory = sqlite3.Row
    
    return conn


@contextmanager
def get_db_context(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    
    Args:
        db_path: Path to database file (defaults to config DATABASE_PATH)
        
    Yields:
        SQLite connection object
        
    Example:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cve LIMIT 10")
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Path | None = None, force: bool = False) -> None:
    """
    Initialize the database with schema.
    
    Args:
        db_path: Path to database file (defaults to config DATABASE_PATH)
        force: If True, delete existing database first
    """
    if db_path is None:
        db_path = DATABASE_PATH
    
    if force and db_path.exists():
        db_path.unlink()
        print(f"Deleted existing database: {db_path}")
    
    conn = get_connection(db_path)
    create_tables(conn)
    conn.close()
    
    print(f"Database initialized: {db_path}")


def vacuum_database(db_path: Path | None = None) -> None:
    """
    Vacuum the database to reclaim space and optimize.
    
    Args:
        db_path: Path to database file (defaults to config DATABASE_PATH)
    """
    if db_path is None:
        db_path = DATABASE_PATH
    
    conn = get_connection(db_path)
    conn.execute("VACUUM")
    conn.close()
    
    print(f"Database vacuumed: {db_path}")
