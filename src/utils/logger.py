import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

class Logger:
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "s3_image_converter") -> logging.Logger:
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance
    
    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        from config.settings import get_settings
        
        settings = get_settings()
        logger = logging.getLogger(name)
        
        # Prevent adding handlers multiple times
        if logger.handlers:
            return logger
        
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Create logs directory if it doesn't exist
        log_dir = Path(settings.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger