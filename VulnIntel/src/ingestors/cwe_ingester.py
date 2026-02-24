"""CWE ingester for MITRE data."""

from pathlib import Path
from typing import List, Dict, Any

from src.config import DATA_SOURCES, UPDATE_INTERVALS, get_cache_path
from src.database.connection import get_db_context
from src.ingestors.base import BaseIngester
from src.parsers.cwe_parser import CWEParser
from src.utils.downloader import download_file
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CWEIngester(BaseIngester):
    """Ingester for CWE data from MITRE."""
    
    def __init__(self) -> None:
        """Initialize CWE ingester."""
        super().__init__("cwe")
        self.parser = CWEParser()
    
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize CWE data from MITRE.
        
        Args:
            force: Force sync even if not due
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            if not force and not self.should_sync(UPDATE_INTERVALS["cwe"]):
                logger.info("CWE sync not needed")
                return True
            
            logger.info("Starting CWE sync")
            
            # Download CWE catalog
            cwe_url = DATA_SOURCES["cwe"]["latest"]
            cache_file = get_cache_path("cwe", "cwec_latest.xml.zip")
            
            xml_file = download_file(cwe_url, cache_file, decompress=True)
            
            # Parse CWE data
            cwe_records = self.parser.parse_file(xml_file)
            
            # Store in database
            self.store_cwes(cwe_records)
            
            self.records_processed = len(cwe_records)
            self.update_sync_metadata("success", UPDATE_INTERVALS["cwe"])
            
            logger.info(f"CWE sync completed: {self.records_processed} records")
            return True
            
        except Exception as e:
            logger.error(f"CWE sync failed: {e}")
            self.errors_encountered += 1
            self.update_sync_metadata("failed")
            return False
    
    def store_cwes(self, cwe_records: List[Dict[str, Any]]) -> None:
        """
        Store CWE records in database.
        
        Args:
            cwe_records: List of parsed CWE records
        """
        logger.info(f"Storing {len(cwe_records)} CWE records")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            for record in cwe_records:
                # Upsert CWE record
                cursor.execute(
                    """
                    INSERT INTO cwe (
                        cwe_id, name, description, abstraction, status,
                        likelihood_of_exploit, common_consequences,
                        applicable_platforms, modes_of_introduction,
                        detection_methods, ingested_at, updated_at
                    ) VALUES (
                        :cwe_id, :name, :description, :abstraction, :status,
                        :likelihood_of_exploit, :common_consequences,
                        :applicable_platforms, :modes_of_introduction,
                        :detection_methods, :ingested_at, :updated_at
                    )
                    ON CONFLICT(cwe_id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        abstraction = excluded.abstraction,
                        status = excluded.status,
                        likelihood_of_exploit = excluded.likelihood_of_exploit,
                        common_consequences = excluded.common_consequences,
                        applicable_platforms = excluded.applicable_platforms,
                        modes_of_introduction = excluded.modes_of_introduction,
                        detection_methods = excluded.detection_methods,
                        updated_at = excluded.updated_at
                    """,
                    record
                )
        
        logger.info(f"Stored {len(cwe_records)} CWE records")
