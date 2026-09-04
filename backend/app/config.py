"""
Application Configuration and Path Settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Varuna AI"
    API_V1_STR: str = "/api"
    
    # Base directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    THUMBNAILS_DIR: Path = DATA_DIR / "thumbnails"
    MODELS_DIR: Path = BASE_DIR / "models"
    SAMPLE_DIR: Path = BASE_DIR / "sample_data"
    
    # Model checkpoint
    MODEL_PATH: Path = MODELS_DIR / "yolov8_varuna.pt"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/varuna.db"
    
    # Sonar defaults
    DEFAULT_SLANT_RANGE_M: float = 75.0
    CONF_THRESHOLD: float = 0.20
    IOU_THRESHOLD: float = 0.40

    class Config:
        case_sensitive = True


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAILS_DIR, exist_ok=True)
os.makedirs(settings.MODELS_DIR, exist_ok=True)
os.makedirs(settings.SAMPLE_DIR, exist_ok=True)
