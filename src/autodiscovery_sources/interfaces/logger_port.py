"""Port for logging operations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LoggerPort(ABC):
    """Port for structured logging."""

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def bind(self, **kwargs: Any) -> "LoggerPort":
        """Create a new logger with bound context."""
        pass

