"""KEV ingester for CISA data."""

from pathlib import Path
from typing import List, Dict, Any

from src.config import DATA_SOURCES, UPDATE_INTERVALS, get_cache_path
from src.database.connection import get_db_context
from src.ingestors.base import BaseIngester
from src.parsers.kev_parser import KEVParser
from src.utils.downloader import download_file
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KEVIngester(BaseIngester):
    """Ingester for KEV data from CISA."""
    
    def __init__(self) -> None:
        """Initialize KEV ingester."""
        super().__init__("kev")
        self.parser = KEVParser()
    
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize KEV data from CISA.
        
        Args:
            force: Force sync even if not due
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            if not force and not self.should_sync(UPDATE_INTERVALS["kev"]):
                logger.info("KEV sync not needed")
                return True
            
            logger.info("Starting KEV sync")
            
            # Download KEV catalog
            kev_url = DATA_SOURCES["kev"]["catalog"]
            cache_file = get_cache_path("kev", "known_exploited_vulnerabilities.json")
            
            json_file = download_file(kev_url, cache_file, decompress=False)
            
            # Parse KEV data
            kev_records = self.parser.parse_file(json_file)
            
            # Store in database
            self.store_kevs(kev_records)
            
            self.records_processed = len(kev_records)
            self.update_sync_metadata("success", UPDATE_INTERVALS["kev"])
            
            logger.info(f"KEV sync completed: {self.records_processed} records")
            return True
            
        except Exception as e:
            logger.error(f"KEV sync failed: {e}")
            self.errors_encountered += 1
            self.update_sync_metadata("failed")
            return False
    
    def store_kevs(self, kev_records: List[Dict[str, Any]]) -> None:
        """
        Store KEV records in database.
        
        Args:
            kev_records: List of parsed KEV records
        """
        logger.info(f"Storing {len(kev_records)} KEV records")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Clear existing KEV entries (full replace strategy)
            cursor.execute("DELETE FROM kev")
            
            # Insert new records
            for record in kev_records:
                cursor.execute(
                    """
                    INSERT INTO kev (
                        cve_id, vendor_project, product, vulnerability_name,
                        date_added, short_description, required_action,
                        due_date, known_ransomware_use, notes,
                        ingested_at, updated_at
                    ) VALUES (
                        :cve_id, :vendor_project, :product, :vulnerability_name,
                        :date_added, :short_description, :required_action,
                        :due_date, :known_ransomware_use, :notes,
                        :ingested_at, :updated_at
                    )
                    """,
                    record
                )
        
        logger.info(f"Stored {len(kev_records)} KEV records")
