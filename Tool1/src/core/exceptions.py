class PredictPathError(Exception):
    """Base exception for PredictPath Tool 1"""
    pass

class SchemaValidationError(PredictPathError):
    """Raised when an event fails strict schema validation."""
    pass

class IngestionError(PredictPathError):
    """Raised during data ingestion failures."""
    pass

class RateLimitExceeded(PredictPathError):
    """Raised when ingestion rate limit is breached."""
    pass

class IntegrityError(PredictPathError):
    """Raised when hash verification or provenance checks fail."""
    pass
