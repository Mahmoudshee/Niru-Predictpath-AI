from typing import Generator, Dict, Any
from .base import BaseIngestor
import polars as pl
import logging

logger = logging.getLogger(__name__)

class CicIdsIngestor(BaseIngestor):
    """
    Ingestor for CIC-IDS Network Flow Logs (CSV).
    """

    def __init__(self, file_path):
        super().__init__(file_path)
        self.parser_version = "cic_ids_v1.0"

    def ingest(self) -> Generator[Dict[str, Any], None, None]:
        try:
             # CIC-IDS usually has headers.
            q = pl.scan_csv(self.file_path, ignore_errors=True)
            
            # Normalize column names to lowercase to avoid issues
            # We will grab specific columns we care about in the normalizer
            for batch in q.collect(streaming=True).iter_rows(named=True):
                yield batch

        except Exception as e:
            logger.error(f"Error reading CIC-IDS file {self.file_path}: {e}")
            raise e
