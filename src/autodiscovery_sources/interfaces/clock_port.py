"""Port for clock/time operations."""

from abc import ABC, abstractmethod
from datetime import datetime


class ClockPort(ABC):
    """Port for getting current time."""

    @abstractmethod
    def now(self) -> datetime:
        """Get current datetime."""
        pass

