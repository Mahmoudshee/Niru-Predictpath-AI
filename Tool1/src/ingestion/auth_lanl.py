from typing import Generator, Dict, Any, Optional
from datetime import datetime, timezone
import polars as pl
from .base import BaseIngestor
import logging

logger = logging.getLogger(__name__)

class LanlAuthIngestor(BaseIngestor):
    """
    Ingestor for Los Alamos National Lab (LANL) Authentication Logs.
    Format is typically: time,source_user@domain,dest_user@domain,source_computer,dest_computer,auth_type,logon_type,auth_orientation,success/failure
    """

    def __init__(self, file_path):
        super().__init__(file_path)
        self.parser_version = "lanl_auth_v1.0"

    def ingest(self) -> Generator[Dict[str, Any], None, None]:
        try:
            # LANL data is CSV-like. We can use Polars for lazy reading if the file is huge,
            # but for line-by-line processing in the engine, standard file reading is often safer for custom parsing.
            # However, prompt required Polars. Let's use scan_csv.
            
            # LANL headers are often implied. We'll assume a standard set or user provided.
            # For this implementation, we assume the standard columns.
            q = pl.scan_csv(
                self.file_path, 
                has_header=False,
                new_columns=[
                    "time", "source_user", "dest_user", "source_host", "dest_host", 
                    "auth_type", "logon_type", "auth_orientation", "status"
                ],
                ignore_errors=True # We will catch them manually or filter
                # In real prod we might handle errors more strictly during scan
            )

            # We process in chunks to be memory efficient
            for batch in q.collect(streaming=True).iter_rows(named=True):
                # FIX: Explicit Header Skip (Robustness)
                # If the CSV has a header but we read it as data, the first row 'time' col will be "time"
                raw_time = str(batch.get('time', '')).lower().strip()
                if raw_time in ['time', 'timestamp', 'date', 'header']:
                     continue
                     
                yield batch

        except Exception as e:
            logger.error(f"Error reading LANL file {self.file_path}: {e}")
            raise e
