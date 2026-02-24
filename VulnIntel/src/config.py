"""Configuration management for VulnIntel."""

import os
from pathlib import Path
from typing import Dict, Any

# Base directories
BASE_DIR = Path(__file__).parent.parent.absolute()
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_DIR = DATA_DIR / "db"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
for directory in [DATA_DIR, CACHE_DIR, DB_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_PATH = DB_DIR / "vuln.db"

# Data source URLs
DATA_SOURCES: Dict[str, Any] = {
    "cve": {
        "recent": "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-recent.json.gz",
        "modified": "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-modified.json.gz",
        "year_template": "https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-{year}.json.gz",
    },
    "cwe": {
        "latest": "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip",
    },
    "kev": {
        "catalog": "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    },
}

# Update intervals (in seconds)
UPDATE_INTERVALS = {
    "cve": 7200,  # 2 hours
    "cwe": 604800,  # 1 week
    "kev": 86400,  # 1 day
}

# Download configuration
DOWNLOAD_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 5,
    "chunk_size": 8192,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Logging configuration
LOG_CONFIG = {
    "file": LOGS_DIR / "vulnintel.log",
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "max_bytes": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5,
}

# Query limits
QUERY_LIMITS = {
    "default_limit": 100,
    "max_limit": 1000,
}


def get_cache_path(source: str, filename: str) -> Path:
    """Get cache file path for a data source."""
    source_dir = CACHE_DIR / source
    source_dir.mkdir(exist_ok=True)
    return source_dir / filename


def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary."""
    return {
        "base_dir": str(BASE_DIR),
        "data_dir": str(DATA_DIR),
        "cache_dir": str(CACHE_DIR),
        "db_dir": str(DB_DIR),
        "logs_dir": str(LOGS_DIR),
        "database_path": str(DATABASE_PATH),
        "data_sources": DATA_SOURCES,
        "update_intervals": UPDATE_INTERVALS,
        "download_config": DOWNLOAD_CONFIG,
        "log_config": LOG_CONFIG,
        "query_limits": QUERY_LIMITS,
    }
