"""CVE ingester for NVD data."""

from pathlib import Path
from typing import List, Dict, Any

from src.config import DATA_SOURCES, UPDATE_INTERVALS, get_cache_path
from src.database.connection import get_db_context
from src.ingestors.base import BaseIngester
from src.parsers.cve_parser import CVEParser
from src.utils.downloader import download_file
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CVEIngester(BaseIngester):
    """Ingester for CVE data from NVD."""
    
    def __init__(self) -> None:
        """Initialize CVE ingester."""
        super().__init__("cve")
        self.parser = CVEParser()
    
    def sync(self, force: bool = False, feed: str = "recent") -> bool:
        """
        Synchronize CVE data from NVD.
        
        Args:
            force: Force sync even if not due
            feed: Feed to sync ("recent", "modified", or year like "2024")
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            if not force and not self.should_sync(UPDATE_INTERVALS["cve"]):
                logger.info("CVE sync not needed")
                return True
            
            logger.info(f"Starting CVE sync (feed: {feed})")
            
            # Download feed
            feed_url = self.get_feed_url(feed)
            cache_file = get_cache_path("cve", f"nvdcve-2.0-{feed}.json.gz")
            
            json_file = download_file(feed_url, cache_file, decompress=True)
            
            # Parse CVE data
            cve_records = self.parser.parse_file(json_file, feed)
            
            # Store in database
            self.store_cves(cve_records)
            
            self.records_processed = len(cve_records)
            self.update_sync_metadata("success", UPDATE_INTERVALS["cve"])
            
            logger.info(f"CVE sync completed: {self.records_processed} records")
            return True
            
        except Exception as e:
            logger.error(f"CVE sync failed: {e}")
            self.errors_encountered += 1
            self.update_sync_metadata("failed")
            return False
    
    def get_feed_url(self, feed: str) -> str:
        """
        Get feed URL for specified feed type.
        
        Args:
            feed: Feed type ("recent", "modified", or year)
            
        Returns:
            Feed URL
        """
        if feed == "recent":
            return DATA_SOURCES["cve"]["recent"]
        elif feed == "modified":
            return DATA_SOURCES["cve"]["modified"]
        else:
            # Assume it's a year
            return DATA_SOURCES["cve"]["year_template"].format(year=feed)
    
    def store_cves(self, cve_records: List[Dict[str, Any]]) -> None:
        """
        Store CVE records in database.
        
        Args:
            cve_records: List of parsed CVE records
        """
        logger.info(f"Storing {len(cve_records)} CVE records")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            for record in cve_records:
                # Extract CWE IDs for mapping
                cwe_ids = record.pop("cwe_ids", [])
                
                # Upsert CVE record
                cursor.execute(
                    """
                    INSERT INTO cve (
                        cve_id, description, published_date, last_modified_date,
                        cvss_v3_score, cvss_v3_severity, cvss_v3_vector,
                        attack_vector, attack_complexity, privileges_required,
                        user_interaction, scope, confidentiality_impact,
                        integrity_impact, availability_impact,
                        affected_cpes, reference_urls, source_feed,
                        ingested_at, updated_at
                    ) VALUES (
                        :cve_id, :description, :published_date, :last_modified_date,
                        :cvss_v3_score, :cvss_v3_severity, :cvss_v3_vector,
                        :attack_vector, :attack_complexity, :privileges_required,
                        :user_interaction, :scope, :confidentiality_impact,
                        :integrity_impact, :availability_impact,
                        :affected_cpes, :reference_urls, :source_feed,
                        :ingested_at, :updated_at
                    )
                    ON CONFLICT(cve_id) DO UPDATE SET
                        description = excluded.description,
                        last_modified_date = excluded.last_modified_date,
                        cvss_v3_score = excluded.cvss_v3_score,
                        cvss_v3_severity = excluded.cvss_v3_severity,
                        cvss_v3_vector = excluded.cvss_v3_vector,
                        attack_vector = excluded.attack_vector,
                        attack_complexity = excluded.attack_complexity,
                        privileges_required = excluded.privileges_required,
                        user_interaction = excluded.user_interaction,
                        scope = excluded.scope,
                        confidentiality_impact = excluded.confidentiality_impact,
                        integrity_impact = excluded.integrity_impact,
                        availability_impact = excluded.availability_impact,
                        affected_cpes = excluded.affected_cpes,
                        reference_urls = excluded.reference_urls,
                        source_feed = excluded.source_feed,
                        updated_at = excluded.updated_at
                    """,
                    record
                )
                
                # Update CVE-CWE mappings
                if cwe_ids:
                    # Delete existing mappings
                    cursor.execute(
                        "DELETE FROM cve_cwe_map WHERE cve_id = ?",
                        (record["cve_id"],)
                    )
                    
                    # Insert new mappings
                    for cwe_id in cwe_ids:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO cve_cwe_map (cve_id, cwe_id)
                            VALUES (?, ?)
                            """,
                            (record["cve_id"], cwe_id)
                        )
        
        logger.info(f"Stored {len(cve_records)} CVE records")
