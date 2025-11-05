"""In-memory adapter for metrics collection."""

from collections import defaultdict
from threading import Lock

from ..interfaces.metrics_port import MetricsPort


class MetricsMemoryAdapter(MetricsPort):
    """In-memory adapter for metrics collection."""

    def __init__(self):
        """Initialize adapter."""
        self._counters: dict = defaultdict(int)
        self._lock = Lock()

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value

    def get_count(self, name: str) -> int:
        """Get current count for a metric."""
        with self._lock:
            return self._counters.get(name, 0)

    def get_all(self) -> dict:
        """Get all metrics."""
        with self._lock:
            return dict(self._counters)

