from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Generator
from pathlib import Path
import polars as pl
from ..core.schema import CanonicalEvent
from ..core.exceptions import IngestionError
import logging

logger = logging.getLogger(__name__)

class BaseIngestor(ABC):
    """
    Abstract Base Class for all Ingestors.
    Enforces a strict interface for reading raw data and yielding intermediate dicts.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        if not self.file_path.exists():
            raise IngestionError(f"File not found: {self.file_path}")
        self.parser_version = "1.0.0" # Default, override in subclasses

    @abstractmethod
    def ingest(self) -> Generator[Dict[str, Any], None, None]:
        """
        Yields raw dictionaries from the source file.
        These dicts are NOT yet CanonicalEvents; they are raw inputs to the normalizer.
        """
        pass

    def estimate_count(self) -> int:
        """Optional: Estimate number of records for progress bars."""
        return 0
