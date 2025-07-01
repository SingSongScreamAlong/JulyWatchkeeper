import logging
import sys
from types import FrameType
from typing import cast

from loguru import logger
from pydantic import BaseModel

from src.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages toward Loguru.
    
    This handler intercepts standard library logging and redirects it to loguru.
    
    See: https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    LOGGER_NAME: str = "watchkeeper"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_LEVEL: str = "INFO"


def setup_logging() -> None:
    """Configure loguru logging."""
    config = LoggingConfig(LOG_LEVEL=settings.LOG_LEVEL)

    # Remove default loguru handler
    logger.remove()
    
    # Add custom handler with specified format
    logger.add(
        sys.stderr,
        format=config.LOG_FORMAT,
        level=config.LOG_LEVEL,
        colorize=True,
    )
    
    # Add file logging
    logger.add(
        "logs/watchkeeper.log",
        rotation="10 MB",
        retention="1 week",
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Update logging levels for some third-party packages
    for logger_name in ("uvicorn", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info("Logging configured successfully")


# Export logger
log = logger
