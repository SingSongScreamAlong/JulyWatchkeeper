"""
Logging configuration for WATCHKEEPER

This module provides a centralized logging configuration for the entire application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with the specified name and configuration
    
    Args:
        name: Name of the logger
        log_file: Path to the log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is provided
    if log_file:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create rotating file handler (10MB max size, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name
    
    Args:
        name: Name of the logger
        
    Returns:
        logging.Logger: Requested logger
    """
    return logging.getLogger(name)
