"""Tests for query API."""

import pytest
from pathlib import Path

from src.query.api import VulnIntelAPI
from src.database.connection import init_database, get_db_context
from src.utils.validators import normalize_cve_id, normalize_cwe_id


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    return db_path


@pytest.fixture
def api(test_db):
    """Create API instance with test database."""
    return VulnIntelAPI(test_db)


def test_api_init(api):
    """Test API initialization."""
    assert api.db_path.exists()


def test_normalize_cve_id():
    """Test CVE ID normalization."""
    assert normalize_cve_id("cve-2024-1234") == "CVE-2024-1234"
    assert normalize_cve_id("CVE-2024-1234") == "CVE-2024-1234"


def test_normalize_cwe_id():
    """Test CWE ID normalization."""
    assert normalize_cwe_id("cwe-79") == "CWE-79"
    assert normalize_cwe_id("CWE-79") == "CWE-79"


def test_get_vuln_stats(api):
    """Test statistics retrieval."""
    stats = api.get_vuln_stats()
    assert "cve" in stats
    assert "cwe" in stats
    assert "kev" in stats


# Add more tests as needed
