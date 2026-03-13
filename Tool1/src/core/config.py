"""
Tool 1 Configuration
"""
import logging
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Base directory layout (relative to this file's location)
# Tool1/src/core/config.py -> Tool1/ is 3 levels up
# ─────────────────────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../Tool1/


class Settings:
    """Simple settings container — no Pydantic, no validation overhead."""

    APP_NAME: str = "PredictPath Tool 1"
    LOG_LEVEL: str = "INFO"
    STRICT_VALIDATION: bool = False
    MAX_INGEST_RATE: int = 1000  # Events per second (token bucket)

    def __init__(self):
        self.BASE_DIR: Path = _BASE_DIR
        self.DATA_DIR: Path = _BASE_DIR / "data"
        self.DEAD_LETTER_QUEUE_DIR: Path = _BASE_DIR / "data" / "dlq"
        self.OUTPUT_DIR: Path = _BASE_DIR / "data" / "output"
        self.MODEL_DIR: Path = _BASE_DIR / "data" / "models"

        # Create directories
        for d in (self.DATA_DIR, self.DEAD_LETTER_QUEUE_DIR, self.OUTPUT_DIR, self.MODEL_DIR):
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass


settings = Settings()


def setup_logging():
    """Configure logging: console always, file when possible."""
    handlers = [logging.StreamHandler()]

    try:
        log_path = settings.BASE_DIR / "tool1.log"
        fh = logging.FileHandler(str(log_path), encoding="utf-8", delay=True)
        handlers.append(fh)
    except Exception:
        pass  # File logging unavailable — continue with console only

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )


setup_logging()
logger = logging.getLogger("predictpath.tool1")
