import logging
import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "PredictPath Tool 1"
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DEAD_LETTER_QUEUE_DIR: Path = DATA_DIR / "dlq"
    OUTPUT_DIR: Path = DATA_DIR / "output"
    MODEL_DIR: Path = DATA_DIR / "models"
    
    # Validation settings
    STRICT_VALIDATION: bool = True
    MAX_INGEST_RATE: int = 1000  # Events per second (Token bucket)

    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DEAD_LETTER_QUEUE_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.BASE_DIR / "tool1.log")
        ]
    )
    logging.info(f"Logging initialized at level {settings.LOG_LEVEL}")

setup_logging()
logger = logging.getLogger("predictpath.tool1")
