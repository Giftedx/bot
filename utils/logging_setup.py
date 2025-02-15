import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging with both file and console handlers"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)s: %(message)s'
    ))
    logger.addHandler(console_handler)

    # File handler with detailed format and rotation
    file_handler = RotatingFileHandler(
        'logs/discord.log',
        maxBytes=5_000_000,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(file_handler)

    return logger