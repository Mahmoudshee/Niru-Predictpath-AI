"""Tests for CVE ingester."""

import pytest
from pathlib import Path

from src.ingestors.cve_ingester import CVEIngester
from src.database.connection import init_database, get_db_context


@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    return db_path


def test_cve_ingester_init():
    """Test CVE ingester initialization."""
    ingester = CVEIngester()
    assert ingester.source_name == "cve"
    assert ingester.parser is not None


def test_get_feed_url():
    """Test feed URL generation."""
    ingester = CVEIngester()
    
    recent_url = ingester.get_feed_url("recent")
    assert "recent" in recent_url
    
    modified_url = ingester.get_feed_url("modified")
    assert "modified" in modified_url
    
    year_url = ingester.get_feed_url("2024")
    assert "2024" in year_url


# Add more tests as needed
