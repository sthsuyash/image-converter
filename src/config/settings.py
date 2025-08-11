from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import os


class Settings(BaseSettings):
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"

    # S3 Configuration
    S3_BUCKET_NAME: str = Field(..., description="S3 bucket name")
    S3_PREFIX: str = Field(default="", description="S3 prefix to filter objects")
    S3_DESTINATION_PREFIX: str = Field(
        default="webp-images", description="Destination prefix for WebP files"
    )

    # Conversion Settings
    WEBP_QUALITY: int = Field(
        default=100, ge=0, le=100, description="WebP quality (0-100)"
    )
    DELETE_ORIGINAL: bool = Field(
        default=False, description="Delete original files after conversion"
    )
    MAX_WORKERS: int = Field(
        default=4, ge=1, le=20, description="Maximum number of worker threads"
    )
    BATCH_SIZE: int = Field(default=100, ge=1, description="Batch size for processing")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/s3_converter.log", description="Log file path")
    LOG_MAX_BYTES: int = Field(
        default=104100760, description="Max log file size in bytes"
    )
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files")

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"
        case_sensitive = True


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
