"""structlog adapter for logging."""

import logging
import os
from typing import Any

import structlog

from ..interfaces.logger_port import LoggerPort


class LoggerStructlogAdapter(LoggerPort):
    """structlog adapter for structured logging."""

    def __init__(self, log_level: str = None):
        """Initialize logger."""
        log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self._logger = structlog.get_logger()

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)

    def bind(self, **kwargs: Any) -> "LoggerPort":
        """Create a new logger with bound context."""
        new_logger = self._logger.bind(**kwargs)
        adapter = LoggerStructlogAdapter()
        adapter._logger = new_logger
        return adapter

