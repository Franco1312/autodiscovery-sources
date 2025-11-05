"""Port for metrics collection."""

from abc import ABC, abstractmethod


class MetricsPort(ABC):
    """Port for metrics collection."""

    @abstractmethod
    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        pass

    @abstractmethod
    def get_count(self, name: str) -> int:
        """Get current count for a metric."""
        pass

    @abstractmethod
    def get_all(self) -> dict:
        """Get all metrics."""
        pass

