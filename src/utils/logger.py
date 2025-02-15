"""Logging configuration for the application."""
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
import json
from datetime import datetime

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        log_format: Optional custom log format
    """
    # Create logs directory if logging to file
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Default format if none provided
    if not log_format:
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    # Basic configuration
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            RichHandler(rich_tracebacks=True, markup=True)
        ]
    )

    # Add file handler if log file specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    # Suppress overly verbose logging from some libraries
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
            
        if hasattr(record, "extra"):
            data["extra"] = record.extra
            
        return json.dumps(data)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent configuration.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Add context info to log records
    extra = {
        "app_name": "repo_analyzer",
        "logger_name": name
    }
    
    logger = logging.LoggerAdapter(logger, extra)
    return logger 