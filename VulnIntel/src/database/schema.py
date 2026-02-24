"""Database schema definitions for VulnIntel."""

import sqlite3
from typing import Any

# SQL schema definitions
SCHEMA_SQL = """
-- CVE table
CREATE TABLE IF NOT EXISTS cve (
    cve_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    published_date TEXT NOT NULL,
    last_modified_date TEXT NOT NULL,
    cvss_v3_score REAL,
    cvss_v3_severity TEXT,
    cvss_v3_vector TEXT,
    attack_vector TEXT,
    attack_complexity TEXT,
    privileges_required TEXT,
    user_interaction TEXT,
    scope TEXT,
    confidentiality_impact TEXT,
    integrity_impact TEXT,
    availability_impact TEXT,
    affected_cpes TEXT,
    reference_urls TEXT,
    source_feed TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cve_published ON cve(published_date);
CREATE INDEX IF NOT EXISTS idx_cve_modified ON cve(last_modified_date);
CREATE INDEX IF NOT EXISTS idx_cve_severity ON cve(cvss_v3_severity);
CREATE INDEX IF NOT EXISTS idx_cve_score ON cve(cvss_v3_score);

-- CWE table
CREATE TABLE IF NOT EXISTS cwe (
    cwe_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    abstraction TEXT,
    status TEXT,
    likelihood_of_exploit TEXT,
    common_consequences TEXT,
    applicable_platforms TEXT,
    modes_of_introduction TEXT,
    detection_methods TEXT,
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cwe_abstraction ON cwe(abstraction);
CREATE INDEX IF NOT EXISTS idx_cwe_likelihood ON cwe(likelihood_of_exploit);

-- KEV table
CREATE TABLE IF NOT EXISTS kev (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cve_id TEXT NOT NULL,
    vendor_project TEXT,
    product TEXT,
    vulnerability_name TEXT,
    date_added TEXT NOT NULL,
    short_description TEXT,
    required_action TEXT,
    due_date TEXT,
    known_ransomware_use TEXT,
    notes TEXT,
    ingested_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_kev_cve ON kev(cve_id);
CREATE INDEX IF NOT EXISTS idx_kev_date_added ON kev(date_added);
CREATE INDEX IF NOT EXISTS idx_kev_ransomware ON kev(known_ransomware_use);

-- CVE-CWE mapping table
CREATE TABLE IF NOT EXISTS cve_cwe_map (
    cve_id TEXT NOT NULL,
    cwe_id TEXT NOT NULL,
    PRIMARY KEY (cve_id, cwe_id)
);

CREATE INDEX IF NOT EXISTS idx_map_cve ON cve_cwe_map(cve_id);
CREATE INDEX IF NOT EXISTS idx_map_cwe ON cve_cwe_map(cwe_id);

-- Sync metadata table
CREATE TABLE IF NOT EXISTS sync_metadata (
    source TEXT PRIMARY KEY,
    last_sync_time TEXT NOT NULL,
    last_sync_status TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    next_sync_due TEXT
);
"""


def create_tables(conn: sqlite3.Connection) -> None:
    """
    Create all database tables and indexes.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_SQL)
    conn.commit()


def get_table_info(conn: sqlite3.Connection, table_name: str) -> list[dict[str, Any]]:
    """
    Get information about a table's columns.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table
        
    Returns:
        List of column information dictionaries
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    return [
        {
            "cid": col[0],
            "name": col[1],
            "type": col[2],
            "notnull": bool(col[3]),
            "default": col[4],
            "pk": bool(col[5]),
        }
        for col in columns
    ]


def get_table_count(conn: sqlite3.Connection, table_name: str) -> int:
    """
    Get row count for a table.
    
    Args:
        conn: SQLite database connection
        table_name: Name of the table
        
    Returns:
        Number of rows in the table
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]


def get_database_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    Get statistics about the database.
    
    Args:
        conn: SQLite database connection
        
    Returns:
        Dictionary with database statistics
    """
    tables = ["cve", "cwe", "kev", "cve_cwe_map", "sync_metadata"]
    stats = {}
    
    for table in tables:
        try:
            stats[table] = get_table_count(conn, table)
        except sqlite3.OperationalError:
            stats[table] = 0
    
    return stats
